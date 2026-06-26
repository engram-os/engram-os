"""Tests for the /chat SSE streaming path.

The non-streaming path is already covered in test_critical_paths.py and
test_multiuser.py. These tests focus purely on the streaming contract.
"""
import json
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

_TEST_USER = "test-user-uuid-0001"  # matches conftest ENGRAM_USER_ID


@pytest.fixture()
def brain_client():
    from core.brain import app
    return TestClient(app)


def _no_match():
    m = MagicMock()
    m.points = []
    return m


def _fake_vec():
    return [0.1] * 768


# ─── Streaming contract ───────────────────────────────────────────────────────

def test_stream_returns_event_stream_content_type(brain_client):
    """`stream: true` → Content-Type is text/event-stream."""
    with patch("api.chat.get_embedding", return_value=_fake_vec()), \
         patch("api.chat.client.search", return_value=_no_match()), \
         patch("api.chat.llm.stream_chat", return_value=iter(["Hi", " there"])):
        resp = brain_client.post("/chat", json={"text": "hello", "stream": True})

    assert resp.status_code == 200
    assert "text/event-stream" in resp.headers["content-type"]


def test_stream_events_contain_delta_tokens(brain_client):
    """Each non-final SSE event carries a non-empty delta."""
    tokens = ["The", " answer", " is", " 42."]
    with patch("api.chat.get_embedding", return_value=_fake_vec()), \
         patch("api.chat.client.search", return_value=_no_match()), \
         patch("api.chat.llm.stream_chat", return_value=iter(tokens)):
        resp = brain_client.post("/chat", json={"text": "what?", "stream": True})

    events = _parse_sse(resp.text)
    delta_events = [e for e in events if not e.get("done")]
    assert len(delta_events) == len(tokens)
    assert [e["delta"] for e in delta_events] == tokens


def test_stream_final_event_has_done_true_and_context_used(brain_client):
    """The last SSE event has `done: true` and a `context_used` list."""
    with patch("api.chat.get_embedding", return_value=_fake_vec()), \
         patch("api.chat.client.search", return_value=_no_match()), \
         patch("api.chat.llm.stream_chat", return_value=iter(["ok"])):
        resp = brain_client.post("/chat", json={"text": "ping", "stream": True})

    events = _parse_sse(resp.text)
    final = events[-1]
    assert final["done"] is True
    assert "context_used" in final


def test_stream_false_returns_json_reply(brain_client):
    """Backward compat: `stream: false` (default) still returns JSON with `reply` key."""
    ollama_resp = MagicMock()
    ollama_resp.json.return_value = {"message": {"content": "pong"}}

    with patch("api.chat.get_embedding", return_value=_fake_vec()), \
         patch("api.chat.client.search", return_value=_no_match()), \
         patch("core.network_gateway.requests.post", return_value=ollama_resp):
        resp = brain_client.post("/chat", json={"text": "ping"})

    assert resp.status_code == 200
    body = resp.json()
    assert "reply" in body
    assert body["reply"] == "pong"


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _parse_sse(text: str) -> list[dict]:
    """Parse raw SSE text into a list of JSON event dicts."""
    events = []
    for block in text.split("\n\n"):
        for line in block.splitlines():
            if line.startswith("data: "):
                try:
                    events.append(json.loads(line[6:]))
                except json.JSONDecodeError:
                    pass
    return events
