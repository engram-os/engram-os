"""tests/test_openai_compat.py — OpenAI-compatible API endpoint tests."""
import json
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

_FAKE_VEC = [0.1] * 768


@pytest.fixture()
def brain_client():
    from core.brain import app
    return TestClient(app)


def _no_match():
    m = MagicMock()
    m.points = []
    return m


def _one_hit(text: str, classification: str = "INTERNAL"):
    point = MagicMock()
    point.payload = {"memory": text, "classification": classification}
    point.score = 0.85
    result = MagicMock()
    result.points = [point]
    return result


# ── /v1/chat/completions ──────────────────────────────────────────────────────

def test_chat_completions_non_streaming_format(brain_client):
    """Non-streaming response matches OpenAI response shape exactly."""
    with patch("api.openai_compat.get_embedding", return_value=_FAKE_VEC), \
         patch("api.openai_compat.client.search", return_value=_no_match()), \
         patch("api.openai_compat.llm.chat", return_value="Hello!"):
        resp = brain_client.post("/v1/chat/completions", json={
            "messages": [{"role": "user", "content": "Hi"}],
        })

    assert resp.status_code == 200
    body = resp.json()
    assert body["object"] == "chat.completion"
    assert "id" in body and body["id"].startswith("chatcmpl-")
    assert "created" in body
    assert body["choices"][0]["message"]["role"] == "assistant"
    assert body["choices"][0]["message"]["content"] == "Hello!"
    assert body["choices"][0]["finish_reason"] == "stop"
    assert "usage" in body


def test_chat_completions_streaming_format(brain_client):
    """Streaming response uses OpenAI chunk format and terminates with [DONE]."""
    tokens = ["The", " sky", " is", " blue."]
    with patch("api.openai_compat.get_embedding", return_value=_FAKE_VEC), \
         patch("api.openai_compat.client.search", return_value=_no_match()), \
         patch("api.openai_compat.llm.stream_chat", return_value=iter(tokens)):
        resp = brain_client.post("/v1/chat/completions", json={
            "messages": [{"role": "user", "content": "What colour is the sky?"}],
            "stream": True,
        })

    assert resp.status_code == 200
    assert "text/event-stream" in resp.headers["content-type"]

    data_lines = [
        line[6:] for line in resp.text.strip().split("\n")
        if line.startswith("data: ")
    ]
    assert data_lines[-1] == "[DONE]"

    chunks = [json.loads(line) for line in data_lines[:-1]]
    assert all(c["object"] == "chat.completion.chunk" for c in chunks)
    token_chunks = [c for c in chunks if c["choices"][0]["delta"].get("content")]
    assert [c["choices"][0]["delta"]["content"] for c in token_chunks] == tokens


def test_chat_completions_rag_context_injected(brain_client):
    """When memories are retrieved, they appear in the system message sent to the LLM."""
    captured = {}

    def fake_chat(messages, model=None):
        captured["messages"] = messages
        return "Answer."

    with patch("api.openai_compat.get_embedding", return_value=_FAKE_VEC), \
         patch("api.openai_compat.client.search", return_value=_one_hit("Client meeting Thursday")), \
         patch("api.openai_compat.llm.chat", side_effect=fake_chat):
        brain_client.post("/v1/chat/completions", json={
            "messages": [{"role": "user", "content": "What's on Thursday?"}],
        })

    system_msgs = [m for m in captured["messages"] if m["role"] == "system"]
    assert len(system_msgs) == 1
    assert "Client meeting Thursday" in system_msgs[0]["content"]


def test_chat_completions_augments_existing_system_message(brain_client):
    """Memory context is appended to an existing system message, not replacing it."""
    captured = {}

    def fake_chat(messages, model=None):
        captured["messages"] = messages
        return "Answer."

    with patch("api.openai_compat.get_embedding", return_value=_FAKE_VEC), \
         patch("api.openai_compat.client.search", return_value=_one_hit("Deposition at 2pm")), \
         patch("api.openai_compat.llm.chat", side_effect=fake_chat):
        brain_client.post("/v1/chat/completions", json={
            "messages": [
                {"role": "system", "content": "You are a legal assistant."},
                {"role": "user", "content": "What's today's schedule?"},
            ],
        })

    system_msgs = [m for m in captured["messages"] if m["role"] == "system"]
    assert len(system_msgs) == 1
    content = system_msgs[0]["content"]
    assert "You are a legal assistant." in content
    assert "Deposition at 2pm" in content


def test_chat_completions_proceeds_without_rag(brain_client):
    """Embedding failure is non-fatal — LLM still called, no system message injected."""
    with patch("api.openai_compat.get_embedding", return_value=None), \
         patch("api.openai_compat.llm.chat", return_value="No context.") as mock_chat:
        resp = brain_client.post("/v1/chat/completions", json={
            "messages": [{"role": "user", "content": "Hello"}],
        })

    assert resp.status_code == 200
    mock_chat.assert_called_once()
    call_messages = mock_chat.call_args.kwargs["messages"]
    system_msgs = [m for m in call_messages if m["role"] == "system"]
    assert len(system_msgs) == 0


# ── /v1/embeddings ────────────────────────────────────────────────────────────

def test_embeddings_single_string(brain_client):
    """Single string input returns one embedding at index 0."""
    vec = [0.5] * 768
    with patch("api.openai_compat.get_embedding", return_value=vec):
        resp = brain_client.post("/v1/embeddings", json={"input": "hello world"})

    assert resp.status_code == 200
    body = resp.json()
    assert body["object"] == "list"
    assert len(body["data"]) == 1
    assert body["data"][0]["object"] == "embedding"
    assert body["data"][0]["index"] == 0
    assert body["data"][0]["embedding"] == vec


def test_embeddings_list_input(brain_client):
    """List of strings returns one embedding per input, in order."""
    vec = [0.1] * 768
    with patch("api.openai_compat.get_embedding", return_value=vec):
        resp = brain_client.post("/v1/embeddings", json={
            "input": ["first", "second", "third"],
        })

    assert resp.status_code == 200
    body = resp.json()
    assert len(body["data"]) == 3
    assert [d["index"] for d in body["data"]] == [0, 1, 2]


def test_embeddings_failure_returns_500(brain_client):
    """get_embedding returning None propagates as HTTP 500."""
    with patch("api.openai_compat.get_embedding", return_value=None):
        resp = brain_client.post("/v1/embeddings", json={"input": "fail this"})

    assert resp.status_code == 500
