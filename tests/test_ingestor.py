"""tests/test_ingestor.py — Unit tests for sensors/ingestor.py improvements.

Covers:
- New plain-text file types (.ts, .html, .xml, .yaml, .yml, .rst)
- .xlsx extraction via openpyxl
- Unsupported extension → quarantine (failed/)
- Parse exception → quarantine (failed/) with _parse_error suffix
- Successful ingest → file moves to processed/
- API error → file stays in inbox/ for retry
"""
import os
import sys
import shutil
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch, mock_open

import pytest

# ── Stub heavy deps before importing ingestor ──────────────────────────────────

# sensors/ingestor.py imports `from core.identity import get_or_create_identity` at
# module level. conftest.py already sets ENGRAM_USER_ID so the real module returns
# without touching the filesystem — no stub needed here.

if "openpyxl" not in sys.modules:
    sys.modules["openpyxl"] = MagicMock()


# ── Helpers ────────────────────────────────────────────────────────────────────

def _make_inbox(tmp_path: Path):
    inbox = tmp_path / "inbox"
    inbox.mkdir()
    processed = inbox / "processed"
    processed.mkdir()
    failed = inbox / "failed"
    failed.mkdir()
    return inbox, processed, failed


# ── extract_text: new plain-text extensions ────────────────────────────────────

@pytest.mark.parametrize("ext", [".ts", ".html", ".xml", ".yaml", ".yml", ".rst"])
def test_extract_text_new_plain_text_types(tmp_path, ext):
    """New plain-text extensions should be read and returned as text."""
    f = tmp_path / f"sample{ext}"
    f.write_text("hello world content", encoding="utf-8")

    from sensors import ingestor
    result = ingestor.extract_text(str(f))

    assert result is not None
    assert "hello world content" in result


def test_extract_text_unsupported_returns_none(tmp_path):
    """An unrecognised extension should return None (triggers quarantine)."""
    f = tmp_path / "binary.exe"
    f.write_bytes(b"\x00\x01\x02")

    from sensors import ingestor
    result = ingestor.extract_text(str(f))

    assert result is None


# ── extract_text: xlsx via openpyxl ───────────────────────────────────────────

def test_extract_text_xlsx(tmp_path):
    """xlsx extraction should concatenate sheet names and cell values."""
    f = tmp_path / "data.xlsx"
    f.write_bytes(b"fake-xlsx-bytes")

    # Build a mock workbook with one sheet and two rows
    mock_sheet = MagicMock()
    mock_sheet.title = "Sheet1"
    mock_sheet.iter_rows.return_value = [
        [MagicMock(value="Name"), MagicMock(value="Age")],
        [MagicMock(value="Alice"), MagicMock(value=30)],
    ]
    mock_wb = MagicMock()
    mock_wb.worksheets = [mock_sheet]

    import openpyxl
    with patch.object(openpyxl, "load_workbook", return_value=mock_wb):
        from sensors import ingestor
        result = ingestor.extract_text(str(f))

    assert result is not None
    assert "Sheet1" in result
    assert "Name" in result
    assert "Alice" in result


# ── scan_inbox: quarantine on unsupported type ─────────────────────────────────

def test_unsupported_file_moves_to_failed(tmp_path):
    """A file with an unrecognised extension should end up in failed/, not processed/."""
    inbox, processed, failed = _make_inbox(tmp_path)
    bad = inbox / "payload.exe"
    bad.write_bytes(b"\x00\x01")

    from sensors import ingestor
    with (
        patch.object(ingestor, "INBOX_DIR", str(inbox)),
        patch.object(ingestor, "PROCESSED_DIR", str(processed)),
        patch.object(ingestor, "FAILED_DIR", str(failed)),
    ):
        ingestor.scan_inbox()

    assert not bad.exists(), "file should have been moved out of inbox"
    assert not (processed / "payload.exe").exists(), "unsupported file must NOT go to processed"
    failed_files = list(failed.iterdir())
    assert len(failed_files) == 1
    assert "payload" in failed_files[0].name and "unsupported" in failed_files[0].name


def test_parse_error_moves_to_failed(tmp_path):
    """A file whose extract_text raises an exception should end up in failed/."""
    inbox, processed, failed = _make_inbox(tmp_path)
    doc = inbox / "corrupt.pdf"
    doc.write_bytes(b"%PDF-broken")

    from sensors import ingestor
    with (
        patch.object(ingestor, "INBOX_DIR", str(inbox)),
        patch.object(ingestor, "PROCESSED_DIR", str(processed)),
        patch.object(ingestor, "FAILED_DIR", str(failed)),
        patch.object(ingestor, "extract_text", side_effect=RuntimeError("parse boom")),
    ):
        ingestor.scan_inbox()

    assert not doc.exists()
    failed_files = list(failed.iterdir())
    assert len(failed_files) == 1
    assert "corrupt" in failed_files[0].name and "parse_error" in failed_files[0].name


# ── scan_inbox: API error leaves file in inbox ─────────────────────────────────

def test_api_error_leaves_file_in_inbox(tmp_path):
    """A non-200 API response is transient — file should stay in inbox for retry."""
    inbox, processed, failed = _make_inbox(tmp_path)
    f = inbox / "note.txt"
    f.write_text("some content")

    mock_resp = MagicMock()
    mock_resp.status_code = 503

    from sensors import ingestor
    with (
        patch.object(ingestor, "INBOX_DIR", str(inbox)),
        patch.object(ingestor, "PROCESSED_DIR", str(processed)),
        patch.object(ingestor, "FAILED_DIR", str(failed)),
        patch.object(ingestor.gateway, "post", return_value=mock_resp),
    ):
        ingestor.scan_inbox()

    assert f.exists(), "file should remain in inbox on transient API error"
    assert not (processed / "note.txt").exists()


# ── scan_inbox: successful ingest moves to processed ──────────────────────────

def test_successful_ingest_moves_to_processed(tmp_path):
    """A 200 response should move the file to processed/."""
    inbox, processed, failed = _make_inbox(tmp_path)
    f = inbox / "report.txt"
    f.write_text("claim number: 2024-AET-001")

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"status": "stored", "id": "abc123"}

    from sensors import ingestor
    with (
        patch.object(ingestor, "INBOX_DIR", str(inbox)),
        patch.object(ingestor, "PROCESSED_DIR", str(processed)),
        patch.object(ingestor, "FAILED_DIR", str(failed)),
        patch.object(ingestor.gateway, "post", return_value=mock_resp),
    ):
        ingestor.scan_inbox()

    assert not f.exists()
    assert (processed / "report.txt").exists()
