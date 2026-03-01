"""
Bootstrap test suite — 5 tests covering the highest-risk paths in Engram OS.

Run with:  pytest tests/ -v
"""
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient


# ─── Shared fixture ───────────────────────────────────────────────────────────

@pytest.fixture()
def brain_client():
    """TestClient for core.brain.app.

    Imported inside the fixture so conftest.py's sys.modules stubs are
    guaranteed to be in place before core.brain is first imported.
    """
    from core.brain import app
    return TestClient(app)


# ─── Test 1: Identity consistency ─────────────────────────────────────────────

def test_identity_consistent_across_calls(monkeypatch, tmp_path):
    """File-based identity: two calls return the same UUID."""
    monkeypatch.delenv("ENGRAM_USER_ID", raising=False)
    monkeypatch.setattr("core.identity.IDENTITY_FILE", str(tmp_path / "identity.json"))

    from core.identity import get_or_create_identity
    id1 = get_or_create_identity()
    id2 = get_or_create_identity()

    assert id1["user_id"] == id2["user_id"]
    assert (tmp_path / "identity.json").exists()


def test_identity_env_var_skips_filesystem(monkeypatch, tmp_path):
    """ENGRAM_USER_ID env var is returned without writing to disk."""
    monkeypatch.setenv("ENGRAM_USER_ID", "fixed-test-uuid-env")
    monkeypatch.setattr("core.identity.IDENTITY_FILE", str(tmp_path / "identity.json"))

    from core.identity import get_or_create_identity
    result = get_or_create_identity()

    assert result["user_id"] == "fixed-test-uuid-env"
    assert not (tmp_path / "identity.json").exists()


# ─── Test 2: Embedding failure handling ───────────────────────────────────────

def test_embedding_failure_returns_error_not_500(brain_client):
    """ConnectionError on Ollama → /chat returns Embedding Error, not a 500."""
    with patch("core.brain.requests.post", side_effect=ConnectionError):
        response = brain_client.post("/chat", json={"text": "hello"})

    assert response.status_code == 200
    assert response.json() == {"reply": "Embedding Error", "context_used": []}


# ─── Test 3: LLM JSON parsing safety ──────────────────────────────────────────

def test_parse_llm_json_extracts_json_from_prose():
    """parse_llm_json succeeds when JSON is embedded in surrounding prose."""
    from agents.tasks import parse_llm_json

    result = parse_llm_json('Sure! {"action": "none"}', "test")
    assert result == {"action": "none"}


def test_parse_llm_json_returns_none_on_unparseable():
    """parse_llm_json returns None (never raises) when there is no JSON."""
    from agents.tasks import parse_llm_json

    result = parse_llm_json("I cannot determine the action.", "test")
    assert result is None


# ─── Test 4: Gmail header safety ──────────────────────────────────────────────

def test_get_header_returns_default_for_empty_list():
    """_get_header on an empty header list returns the default without raising."""
    from agents.gmail_tools import _get_header

    result = _get_header([], "Subject", "(No Subject)")
    assert result == "(No Subject)"


# ─── Test 5: Ingest deduplication ─────────────────────────────────────────────

def test_ingest_deduplication(brain_client):
    """Second identical POST /ingest returns duplicate_skipped."""
    fake_vector = [0.1] * 768

    embed_response = MagicMock()
    embed_response.json.return_value = {"embedding": fake_vector}

    no_match = MagicMock()
    no_match.points = []

    mock_hit = MagicMock()
    mock_hit.id = "dedup-test-point-id"
    mock_hit.score = 0.99
    has_match = MagicMock()
    has_match.points = [mock_hit]

    with patch("core.brain.requests.post", return_value=embed_response), \
         patch("core.brain.client.query_points", side_effect=[no_match, has_match]), \
         patch("core.brain.client.upsert"):

        r1 = brain_client.post("/ingest", json={"text": "unique memory about the project"})
        r2 = brain_client.post("/ingest", json={"text": "unique memory about the project"})

    assert r1.json()["status"] == "raw_data_saved"
    assert r2.json()["status"] == "duplicate_skipped"
