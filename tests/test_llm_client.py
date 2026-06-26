"""Tests for core/llm_client.py — OllamaEngine + LLMEngine Protocol."""
from unittest.mock import MagicMock

from core.llm_client import LLMEngine, OllamaEngine


def _make_engine():
    gw = MagicMock()
    return OllamaEngine(gw, default_model="llama3.1:latest"), gw


def test_ollama_engine_satisfies_protocol():
    engine, _ = _make_engine()
    assert isinstance(engine, LLMEngine)


def test_embed_returns_vector_on_success():
    engine, gw = _make_engine()
    resp = MagicMock()
    resp.json.return_value = {"embedding": [0.1, 0.2, 0.3]}
    gw.post.return_value = resp

    result = engine.embed("hello world")

    assert result == [0.1, 0.2, 0.3]
    gw.post.assert_called_once()
    call_json = gw.post.call_args.kwargs["json"]
    assert call_json["model"] == "nomic-embed-text:latest"
    assert call_json["prompt"] == "hello world"


def test_embed_returns_none_on_connection_error():
    engine, gw = _make_engine()
    gw.post.side_effect = ConnectionError("refused")

    assert engine.embed("hello") is None


def test_embed_returns_none_on_missing_key():
    engine, gw = _make_engine()
    resp = MagicMock()
    resp.json.return_value = {"unexpected": "shape"}
    gw.post.return_value = resp

    assert engine.embed("hello") is None


def test_chat_returns_content_on_success():
    engine, gw = _make_engine()
    resp = MagicMock()
    resp.json.return_value = {"message": {"content": "The answer is 42."}}
    gw.post.return_value = resp

    result = engine.chat([{"role": "user", "content": "What is the answer?"}])

    assert result == "The answer is 42."


def test_chat_uses_default_model_when_none_passed():
    engine, gw = _make_engine()
    resp = MagicMock()
    resp.json.return_value = {"message": {"content": "ok"}}
    gw.post.return_value = resp

    engine.chat([{"role": "user", "content": "hi"}])

    sent_model = gw.post.call_args.kwargs["json"]["model"]
    assert sent_model == "llama3.1:latest"


def test_chat_uses_override_model_when_passed():
    engine, gw = _make_engine()
    resp = MagicMock()
    resp.json.return_value = {"message": {"content": "ok"}}
    gw.post.return_value = resp

    engine.chat([{"role": "user", "content": "hi"}], model="mistral:latest")

    sent_model = gw.post.call_args.kwargs["json"]["model"]
    assert sent_model == "mistral:latest"


def test_chat_returns_none_on_connection_error():
    engine, gw = _make_engine()
    gw.post.side_effect = ConnectionError("refused")

    assert engine.chat([{"role": "user", "content": "hi"}]) is None
