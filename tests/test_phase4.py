"""Tests for Phase 4 reliability changes.

Covers:
- REL-9: PDF parse timeout via ThreadPoolExecutor
- REL-10: Crawler duplicate URL queue (queued set)
- REL-11: Crawler 4xx/5xx retry logic

Import notes:
- sensors/* use `from identity import get_or_create_identity` which resolves
  from core/ (added to PYTHONPATH at runtime but not in tests). Stubbed below.
- tools.crawler is stubbed in conftest (module-level Qdrant connection).
  Tests that need the real module pop the stub and restore it after.
"""
import sys
import time
from unittest.mock import MagicMock, patch

import pytest

# ── Stub `identity` so sensors can be imported ────────────────────────────────
# sensors/ingestor.py calls get_or_create_identity() at module level.
# `identity` lives in core/ which isn't on the test PYTHONPATH.
if "identity" not in sys.modules:
    _id_stub = MagicMock()
    _id_stub.get_or_create_identity.return_value = {"user_id": "test-user-uuid-0001"}
    sys.modules["identity"] = _id_stub


# ── Fixture: real tools.crawler (bypasses conftest stub) ──────────────────────

@pytest.fixture
def real_crawler():
    """Pop the conftest MagicMock stub, import the real tools.crawler module
    (qdrant_client + bs4 are already MagicMock-stubbed by conftest so the
    module-level _ensure_doc_collection() call succeeds without a real connection),
    yield the module, then restore the stub so other tests are unaffected.
    """
    import importlib
    stub = sys.modules.pop("tools.crawler", None)
    try:
        mod = importlib.import_module("tools.crawler")
        yield mod
    finally:
        sys.modules.pop("tools.crawler", None)
        if stub is not None:
            sys.modules["tools.crawler"] = stub


# ─── REL-9: PDF parse timeout ─────────────────────────────────────────────────

class TestPDFTimeout:

    def test_pdf_timeout_returns_none_and_logs(self, caplog, tmp_path):
        """When _parse_pdf exceeds the timeout, extract_text returns None."""
        import importlib, logging
        # Reload so module-level code (IDENTITY) runs with identity stub in place
        stub = sys.modules.pop("sensors.ingestor", None)
        try:
            ing = importlib.import_module("sensors.ingestor")
        except Exception:
            if stub:
                sys.modules["sensors.ingestor"] = stub
            raise

        dummy_pdf = tmp_path / "hang.pdf"
        dummy_pdf.write_bytes(b"%PDF-1.4\n%%EOF")  # minimal syntactically valid PDF

        def slow_parse(filepath, filename):
            time.sleep(0.5)  # longer than the patched 0.1s timeout
            return f"File '{filename}': "

        with patch.object(ing, "_parse_pdf", side_effect=slow_parse):
            with patch.object(ing, "_PDF_PARSE_TIMEOUT", 0.1):
                with caplog.at_level(logging.ERROR, logger="sensors.ingestor"):
                    result = ing.extract_text(str(dummy_pdf))

        assert result is None
        assert any("timed out" in r.message.lower() for r in caplog.records)

        # Restore / clean up
        sys.modules.pop("sensors.ingestor", None)
        if stub:
            sys.modules["sensors.ingestor"] = stub

    def test_fast_pdf_returns_string(self, tmp_path):
        """A PDF that parses quickly returns a string, not None."""
        import importlib
        stub = sys.modules.pop("sensors.ingestor", None)
        try:
            ing = importlib.import_module("sensors.ingestor")
        except Exception:
            if stub:
                sys.modules["sensors.ingestor"] = stub
            raise

        dummy_pdf = tmp_path / "fast.pdf"
        dummy_pdf.write_bytes(b"%PDF-1.4\n%%EOF")

        result = ing.extract_text(str(dummy_pdf))
        # pypdf is MagicMock in conftest → pages yields nothing → returns empty string
        assert isinstance(result, str)
        assert "fast.pdf" in result

        sys.modules.pop("sensors.ingestor", None)
        if stub:
            sys.modules["sensors.ingestor"] = stub


# ─── REL-10: Crawler duplicate URL queue ──────────────────────────────────────

class TestCrawlerDuplicateQueue:

    def test_queued_set_initialised_with_base_url(self, real_crawler):
        sp = real_crawler.DocSpider("http://docs.example.com/", max_pages=10)
        assert "http://docs.example.com/" in sp.queued

    def test_is_valid_url_rejects_already_queued(self, real_crawler):
        sp = real_crawler.DocSpider("http://docs.example.com/", max_pages=10)
        # base URL is already in queued — must be rejected
        assert not sp.is_valid_url("http://docs.example.com/")

    def test_is_valid_url_accepts_new_same_domain_url(self, real_crawler):
        sp = real_crawler.DocSpider("http://docs.example.com/", max_pages=10)
        assert sp.is_valid_url("http://docs.example.com/page2")

    def test_is_valid_url_rejects_external_domain(self, real_crawler):
        sp = real_crawler.DocSpider("http://docs.example.com/", max_pages=10)
        assert not sp.is_valid_url("http://evil.com/malicious")

    def test_same_url_never_enqueued_twice(self, real_crawler):
        """is_valid_url returns False after the first enqueue, so the same URL
        found multiple times on a page is added to queued exactly once.

        Tests the invariant directly without needing a real BeautifulSoup parse
        (bs4 is MagicMock-stubbed in conftest and can't parse HTML in tests).
        """
        sp = real_crawler.DocSpider("http://docs.example.com/", max_pages=10)
        # Simulate finding the same link 3 times (as the crawl loop does)
        for _ in range(3):
            url = "http://docs.example.com/page2"
            if sp.is_valid_url(url):
                sp.queued.add(url)
        assert sp.queued == {"http://docs.example.com/", "http://docs.example.com/page2"}


# ─── REL-11: Crawler retry logic ──────────────────────────────────────────────

class TestCrawlerRetry:

    def test_5xx_retried_max_times(self, real_crawler):
        """A page that always returns 503 is attempted _MAX_RETRIES times."""
        sp = real_crawler.DocSpider("http://docs.example.com/", max_pages=10)
        call_count = 0

        # gateway.get is called as gateway.get("crawler", url, timeout=5) — the
        # mock receives ("crawler", url_str) as positional + timeout=5 as keyword.
        # Use *args/**kwargs to avoid the "multiple values for timeout" TypeError.
        def always_503(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            r = MagicMock()
            r.status_code = 503
            return r

        with patch.object(real_crawler.gateway, "get", side_effect=always_503):
            with patch("tools.crawler.time.sleep"):  # skip actual backoff sleep
                sp._fetch_with_retry("http://docs.example.com/bad")

        assert call_count == real_crawler._MAX_RETRIES

    def test_4xx_not_retried(self, real_crawler):
        """A 404 response is returned immediately — no retries."""
        sp = real_crawler.DocSpider("http://docs.example.com/", max_pages=10)
        call_count = 0

        def not_found(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            r = MagicMock()
            r.status_code = 404
            return r

        with patch.object(real_crawler.gateway, "get", side_effect=not_found):
            resp = sp._fetch_with_retry("http://docs.example.com/gone")

        assert call_count == 1
        assert resp.status_code == 404

    def test_200_returned_without_retry(self, real_crawler):
        """A 200 on the first attempt is returned immediately."""
        sp = real_crawler.DocSpider("http://docs.example.com/", max_pages=10)
        ok = MagicMock()
        ok.status_code = 200
        ok.content = b"<html></html>"

        with patch.object(real_crawler.gateway, "get", return_value=ok) as mock_get:
            resp = sp._fetch_with_retry("http://docs.example.com/ok")

        assert resp.status_code == 200
        assert mock_get.call_count == 1
