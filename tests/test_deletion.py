"""
tests/test_deletion.py — DSE-3: Memory deletion endpoint tests.

Covers:
  - DELETE /api/memory/{point_id}  (single point)
  - DELETE /api/memories           (batch by matter_id + optional type)

Run with: pytest tests/ -v
"""
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

_VALID_UUID = "550e8400-e29b-41d4-a716-446655440000"
_TEST_USER  = "test-user-uuid-0001"   # matches conftest ENGRAM_USER_ID


@pytest.fixture()
def brain_client():
    from core.brain import app
    return TestClient(app)


# ─── DELETE /api/memory/{point_id} ────────────────────────────────────────────

def test_delete_memory_not_found(brain_client):
    """retrieve() returns empty list → 404."""
    with patch("core.brain.client._qdrant.retrieve", return_value=[]):
        resp = brain_client.delete(f"/api/memory/{_VALID_UUID}")
    assert resp.status_code == 404


def test_delete_memory_wrong_user(brain_client):
    """Point exists but user_id in payload doesn't match current user → 403."""
    mock_point = MagicMock()
    mock_point.payload = {"user_id": "someone-else", "matter_id": ""}

    with patch("core.brain.client._qdrant.retrieve", return_value=[mock_point]):
        resp = brain_client.delete(f"/api/memory/{_VALID_UUID}")
    assert resp.status_code == 403


def test_delete_memory_success(brain_client):
    """Valid ownership → delete() called, audit log emitted, 200 returned."""
    mock_point = MagicMock()
    mock_point.payload = {"user_id": _TEST_USER, "matter_id": "m1"}

    with patch("core.brain.client._qdrant.retrieve", return_value=[mock_point]), \
         patch("core.brain.client._qdrant.delete") as mock_delete, \
         patch("core.brain.log_agent_action") as mock_log:
        resp = brain_client.delete(f"/api/memory/{_VALID_UUID}")

    assert resp.status_code == 200
    assert resp.json()["status"] == "deleted"
    assert resp.json()["id"] == _VALID_UUID
    mock_delete.assert_called_once()
    mock_log.assert_called_once()
    # action_type is the 2nd positional arg to log_agent_action
    assert mock_log.call_args.args[1] == "DELETE"
    assert mock_log.call_args.kwargs["resource_id"] == _VALID_UUID


def test_delete_memory_invalid_uuid(brain_client):
    """Non-UUID point_id → 422 before any Qdrant call."""
    with patch("core.brain.client._qdrant.retrieve") as mock_retrieve:
        resp = brain_client.delete("/api/memory/not-a-valid-uuid")
    assert resp.status_code == 422
    mock_retrieve.assert_not_called()


# ─── DELETE /api/memories (batch) ─────────────────────────────────────────────

def test_delete_memories_missing_matter_id(brain_client):
    """matter_id query param is required — omitting it returns 422."""
    resp = brain_client.delete("/api/memories")
    assert resp.status_code == 422


def test_delete_memories_batch_with_type(brain_client):
    """Batch delete with type filter: delete() called, DELETE_BATCH audit emitted."""
    with patch("core.brain.client._qdrant.delete") as mock_delete, \
         patch("core.brain.log_agent_action") as mock_log, \
         patch("core.brain._resolve_matter", return_value="matter-123"):
        resp = brain_client.delete(
            "/api/memories",
            params={"matter_id": "matter-123", "type": "file_ingest"},
        )

    assert resp.status_code == 200
    assert resp.json()["status"] == "deleted"
    mock_delete.assert_called_once()
    mock_log.assert_called_once()
    assert mock_log.call_args.args[1] == "DELETE_BATCH"
