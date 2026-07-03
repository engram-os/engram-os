import json
import logging
import os
import time
import uuid
from typing import Generator

from fastapi import APIRouter, Depends, HTTPException, Request, Security
from fastapi.responses import StreamingResponse
from fastapi.security import APIKeyHeader, HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel
from qdrant_client.http import models

from core.auth import LOCAL_USER_ID
from core.classification_engine import classify
from core.deps import COLLECTION_NAME, LLM_MODEL, client, get_embedding, llm
from core.sanitizer import sanitize
from core.user_registry import User, get_user_by_key

logger = logging.getLogger(__name__)
router = APIRouter()

_bearer_scheme = HTTPBearer(auto_error=False)
_api_key_scheme = APIKeyHeader(name="X-API-Key", auto_error=False)

MAX_CONTEXT_CHARS = 3000


def _get_openai_user(
    bearer: HTTPAuthorizationCredentials | None = Security(_bearer_scheme),
    api_key: str | None = Security(_api_key_scheme),
) -> User:
    """Accept Authorization: Bearer <key> (OpenAI clients) or X-API-Key (Engram clients)."""
    engram_api_key = os.getenv("ENGRAM_API_KEY")
    if not engram_api_key:
        return User(id=LOCAL_USER_ID, role="admin", display_name="local-admin")
    raw_key = (bearer.credentials if bearer else None) or api_key
    if not raw_key:
        raise HTTPException(status_code=403, detail="Authorization required.")
    user = get_user_by_key(raw_key)
    if not user:
        raise HTTPException(status_code=403, detail="Invalid API key.")
    return user


# ── Request / response models ─────────────────────────────────────────────────

class CompletionMessage(BaseModel):
    role: str
    content: str


class CompletionRequest(BaseModel):
    model: str | None = None
    messages: list[CompletionMessage]
    stream: bool = False
    max_tokens: int | None = None  # accepted, not forwarded — Ollama manages this


class EmbeddingRequest(BaseModel):
    input: str | list[str]
    model: str | None = None


# ── Helpers ───────────────────────────────────────────────────────────────────

def _chat_id() -> str:
    return f"chatcmpl-{uuid.uuid4().hex[:12]}"


def _chunk(chat_id: str, model: str, delta: dict, finish_reason: str | None = None) -> str:
    payload = {
        "id": chat_id,
        "object": "chat.completion.chunk",
        "created": int(time.time()),
        "model": model,
        "choices": [{"index": 0, "delta": delta, "finish_reason": finish_reason}],
    }
    return f"data: {json.dumps(payload)}\n\n"


def _build_rag_messages(
    messages: list[CompletionMessage],
    user_id: str,
    matter_id: str | None,
) -> list[dict]:
    """Retrieve relevant memories and inject them into the message list.

    Returns the original messages unchanged if embedding or search fails —
    the LLM is still called without context rather than raising an error.
    """
    query = next((m.content for m in reversed(messages) if m.role == "user"), None)
    context_str = ""

    if query:
        vector = get_embedding(query)
        if vector:
            try:
                must = [models.FieldCondition(key="user_id", match=models.MatchValue(value=user_id))]
                if matter_id:
                    must.append(models.FieldCondition(
                        key="matter_id", match=models.MatchValue(value=matter_id)
                    ))
                result = client.search(
                    collection_name=COLLECTION_NAME,
                    query_vector=vector,
                    query_filter=models.Filter(must=must),
                    limit=5,
                    score_threshold=0.45,
                )
                lines = []
                for hit in result.points:
                    mem = hit.payload.get("memory", "")
                    clf = classify(mem)
                    sanitized = sanitize(mem, clf)
                    lines.append(f"- {sanitized.text}")
                context_str = "\n".join(lines)[:MAX_CONTEXT_CHARS]
            except Exception as e:
                logger.warning(f"RAG retrieval failed (non-fatal): {e}")

    augmented = [{"role": m.role, "content": m.content} for m in messages]

    if context_str:
        memory_block = (
            "The following memories from your personal knowledge base are relevant:\n"
            + context_str
        )
        system_idx = next((i for i, m in enumerate(augmented) if m["role"] == "system"), None)
        if system_idx is not None:
            augmented[system_idx]["content"] += f"\n\n{memory_block}"
        else:
            augmented.insert(0, {"role": "system", "content": memory_block})

    return augmented


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/v1/chat/completions")
def chat_completions(
    request: Request,
    item: CompletionRequest,
    current_user: User = Depends(_get_openai_user),
):
    model = item.model or LLM_MODEL
    matter_id = request.headers.get("X-Matter-ID")
    augmented = _build_rag_messages(item.messages, current_user.id, matter_id)

    if item.stream:
        chat_id = _chat_id()

        def _stream() -> Generator[str, None, None]:
            yield _chunk(chat_id, model, {"role": "assistant", "content": ""})
            try:
                for token in llm.stream_chat(augmented, model=model):
                    yield _chunk(chat_id, model, {"content": token})
            except Exception as e:
                logger.error(f"Stream error: {e}")
            yield _chunk(chat_id, model, {}, finish_reason="stop")
            yield "data: [DONE]\n\n"

        return StreamingResponse(
            _stream(),
            media_type="text/event-stream",
            headers={"X-Accel-Buffering": "no", "Cache-Control": "no-cache"},
        )

    reply = llm.chat(messages=augmented, model=model)
    if reply is None:
        raise HTTPException(status_code=500, detail="LLM inference failed.")

    return {
        "id": _chat_id(),
        "object": "chat.completion",
        "created": int(time.time()),
        "model": model,
        "choices": [{
            "index": 0,
            "message": {"role": "assistant", "content": reply},
            "finish_reason": "stop",
        }],
        "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
    }


@router.post("/v1/embeddings")
def embeddings(
    item: EmbeddingRequest,
    current_user: User = Depends(_get_openai_user),
):
    inputs = [item.input] if isinstance(item.input, str) else item.input
    data = []
    for i, text in enumerate(inputs):
        vector = get_embedding(text)
        if vector is None:
            raise HTTPException(status_code=500, detail=f"Embedding failed for input at index {i}.")
        data.append({"object": "embedding", "embedding": vector, "index": i})

    return {
        "object": "list",
        "data": data,
        "model": item.model or "nomic-embed-text",
        "usage": {"prompt_tokens": 0, "total_tokens": 0},
    }
