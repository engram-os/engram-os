"""tests/test_memory_browser.py — Tests for GET /api/memories scroll endpoint."""
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def brain_client():
    from core.brain import app
    return TestClient(app)


class _Point:
    def __init__(self, point_id, payload):
        self.id = point_id
        self.payload = payload


def _scroll_result(points, next_offset=None):
    return (points, next_offset)


# ── GET /api/memories ─────────────────────────────────────────────────────────

def test_memories_list_returns_correct_shape(brain_client):
    """Response contains a memories list and next_offset field."""
    points = [
        _Point("id-1", {
            "memory": "Client call at 3pm",
            "type": "explicit_memory",
            "matter_id": "m-1",
            "classification": "INTERNAL",
            "created_at": "2026-03-07 10:00:00",
        }),
        _Point("id-2", {
            "memory": "Invoice due Friday",
            "type": "file_ingest",
            "matter_id": "",
            "classification": "CONFIDENTIAL",
            "created_at": "2026-03-07 11:00:00",
        }),
    ]
    with patch("api.memory.client.scroll", return_value=_scroll_result(points)):
        resp = brain_client.get("/api/memories")

    assert resp.status_code == 200
    body = resp.json()
    assert "memories" in body
    assert "next_offset" in body
    assert len(body["memories"]) == 2

    first = body["memories"][0]
    assert first["id"] == "id-1"
    assert first["memory"] == "Client call at 3pm"
    assert first["type"] == "explicit_memory"
    assert first["classification"] == "INTERNAL"
    assert first["matter_id"] == "m-1"


def test_memories_list_empty(brain_client):
    """Empty scroll returns empty list with null next_offset."""
    with patch("api.memory.client.scroll", return_value=_scroll_result([])):
        resp = brain_client.get("/api/memories")

    assert resp.status_code == 200
    body = resp.json()
    assert body["memories"] == []
    assert body["next_offset"] is None


def test_memories_list_type_filter_forwarded(brain_client):
    """type query param is applied as a Qdrant filter condition."""
    with patch("api.memory.client.scroll", return_value=_scroll_result([])) as mock_scroll:
        brain_client.get("/api/memories?type=file_ingest")

    mock_scroll.assert_called_once()
    scroll_filter = mock_scroll.call_args.kwargs.get("scroll_filter") \
        or mock_scroll.call_args.args[1]
    assert scroll_filter is not None


def test_memories_list_offset_forwarded(brain_client):
    """offset query param is passed through to client.scroll."""
    cursor = "abc12345-0000-0000-0000-000000000000"
    with patch("api.memory.client.scroll", return_value=_scroll_result([], None)) as mock_scroll:
        brain_client.get(f"/api/memories?offset={cursor}")

    mock_scroll.assert_called_once()
    call_kwargs = mock_scroll.call_args.kwargs
    assert call_kwargs.get("offset") == cursor
