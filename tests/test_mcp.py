"""tests/test_mcp.py — Unit tests for MCP server tool functions."""
from unittest.mock import MagicMock, patch


class _Point:
    def __init__(self, point_id, score, payload):
        self.id = point_id
        self.score = score
        self.payload = payload


class _SearchResult:
    def __init__(self, points):
        self.points = points


# ── memory_search ─────────────────────────────────────────────────────────────

@patch("api.mcp_server.client")
@patch("api.mcp_server.get_embedding")
def test_memory_search_returns_hits(mock_embed, mock_client):
    from api.mcp_server import memory_search
    mock_embed.return_value = [0.1, 0.2, 0.3]
    mock_client.search.return_value = _SearchResult([
        _Point("id-1", 0.87, {"memory": "Appointment Tuesday 3pm", "matter_id": "m-1", "classification": "PHI"}),
        _Point("id-2", 0.72, {"memory": "Call billing team", "matter_id": "", "classification": "INTERNAL"}),
    ])
    result = memory_search("appointment")
    assert len(result) == 2
    assert result[0]["memory"] == "Appointment Tuesday 3pm"
    assert result[0]["score"] == 0.87
    assert result[0]["classification"] == "PHI"
    assert result[0]["matter_id"] == "m-1"
    mock_embed.assert_called_once_with("appointment")


@patch("api.mcp_server.client")
@patch("api.mcp_server.get_embedding")
def test_memory_search_empty(mock_embed, mock_client):
    from api.mcp_server import memory_search
    mock_embed.return_value = [0.1, 0.2, 0.3]
    mock_client.search.return_value = _SearchResult([])
    assert memory_search("nothing stored") == []


@patch("api.mcp_server.get_embedding")
def test_memory_search_embedding_failure_returns_empty(mock_embed):
    from api.mcp_server import memory_search
    mock_embed.return_value = None
    result = memory_search("query")
    assert result == []


@patch("api.mcp_server.client")
@patch("api.mcp_server.get_embedding")
def test_memory_search_passes_matter_filter(mock_embed, mock_client):
    from api.mcp_server import memory_search
    mock_embed.return_value = [0.1, 0.2, 0.3]
    mock_client.search.return_value = _SearchResult([])
    memory_search("query", matter_id="m-abc")
    mock_client.search.assert_called_once()
    kwargs = mock_client.search.call_args.kwargs
    assert kwargs["query_filter"] is not None


# ── memory_ingest ─────────────────────────────────────────────────────────────

@patch("api.mcp_server.classify")
@patch("api.mcp_server.client")
@patch("api.mcp_server.get_embedding")
def test_memory_ingest_success(mock_embed, mock_client, mock_classify):
    from api.mcp_server import memory_ingest
    mock_embed.return_value = [0.1, 0.2, 0.3]
    clf = MagicMock()
    clf.name = "INTERNAL"
    mock_classify.return_value = clf

    result = memory_ingest("Team standup at 10am")

    assert result["status"] == "stored"
    assert "id" in result
    mock_client.write.assert_called_once()
    write_kwargs = mock_client.write.call_args.kwargs
    assert write_kwargs["classification"] == "INTERNAL"
    assert write_kwargs["payload"]["memory"] == "Team standup at 10am"
    assert write_kwargs["payload"]["type"] == "explicit_memory"


@patch("api.mcp_server.get_embedding")
def test_memory_ingest_embedding_failure(mock_embed):
    from api.mcp_server import memory_ingest
    mock_embed.return_value = None
    result = memory_ingest("text that fails to embed")
    assert result["status"] == "error"
    assert "embedding" in result["reason"]


# ── memory_matters ────────────────────────────────────────────────────────────

@patch("api.mcp_server.list_matters_for_user")
def test_memory_matters_returns_list(mock_list):
    from api.mcp_server import memory_matters
    mock_list.return_value = [
        {"id": "m-1", "name": "Smith Case", "status": "open", "created_by": "u", "created_at": "now"},
        {"id": "m-2", "name": "Doe Project", "status": "open", "created_by": "u", "created_at": "now"},
    ]
    result = memory_matters()
    assert len(result) == 2
    assert result[0] == {"id": "m-1", "name": "Smith Case"}
    assert result[1] == {"id": "m-2", "name": "Doe Project"}


# ── memory_resource ───────────────────────────────────────────────────────────

@patch("api.mcp_server.client")
def test_memory_resource_formats_output(mock_client):
    from api.mcp_server import memory_resource
    mock_client.scroll.return_value = (
        [
            _Point("id-1", 1.0, {"memory": "Prior auth denied for MRI", "classification": "PHI"}),
            _Point("id-2", 1.0, {"memory": "Resubmit by March 15", "classification": "CONFIDENTIAL"}),
        ],
        None,
    )
    result = memory_resource("m-123")
    assert "Prior auth denied for MRI" in result
    assert "Resubmit by March 15" in result
    assert "PHI" in result


@patch("api.mcp_server.client")
def test_memory_resource_empty_matter(mock_client):
    from api.mcp_server import memory_resource
    mock_client.scroll.return_value = ([], None)
    result = memory_resource("empty-matter")
    assert "No memories" in result
