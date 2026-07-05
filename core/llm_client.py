import json
import logging
from typing import Iterator, Protocol, runtime_checkable

logger = logging.getLogger(__name__)

# Keep models resident in RAM between requests. Ollama's default is 5 minutes,
# after which the next request pays a full model reload from disk.
KEEP_ALIVE = "30m"


@runtime_checkable
class LLMEngine(Protocol):
    """Minimal interface for LLM inference. Concrete engines swap in without touching callers."""

    def embed(self, text: str) -> list[float] | None: ...
    def chat(self, messages: list[dict], model: str | None = None) -> str | None: ...
    def stream_chat(self, messages: list[dict], model: str | None = None) -> Iterator[str]: ...


class OllamaEngine:
    """LLMEngine backed by a local Ollama instance via NetworkGateway."""

    def __init__(self, gateway, default_model: str) -> None:
        self._gateway = gateway
        self._default_model = default_model

    def embed(self, text: str) -> list[float] | None:
        try:
            res = self._gateway.post(
                "ollama", "/api/embeddings",
                json={"model": "nomic-embed-text:latest", "prompt": text, "keep_alive": KEEP_ALIVE},
                timeout=30,
            )
            return res.json()["embedding"]
        except Exception as e:
            logger.error(f"Embedding failed: {e}")
            return None

    def chat(self, messages: list[dict], model: str | None = None) -> str | None:
        try:
            res = self._gateway.post(
                "ollama", "/api/chat",
                json={
                    "model": model or self._default_model,
                    "messages": messages,
                    "stream": False,
                    "keep_alive": KEEP_ALIVE,
                },
                timeout=60,
            )
            return res.json()["message"]["content"]
        except Exception as e:
            logger.error(f"Chat failed: {e}")
            return None

    def stream_chat(self, messages: list[dict], model: str | None = None) -> Iterator[str]:
        try:
            resp = self._gateway.post(
                "ollama", "/api/chat",
                json={
                    "model": model or self._default_model,
                    "messages": messages,
                    "stream": True,
                    "keep_alive": KEEP_ALIVE,
                },
                stream=True,
                timeout=60,
            )
            for line in resp.iter_lines():
                if not line:
                    continue
                chunk = json.loads(line)
                content = chunk.get("message", {}).get("content", "")
                if content:
                    yield content
                if chunk.get("done"):
                    break
        except Exception as e:
            logger.error(f"Stream chat failed: {e}")
            return
