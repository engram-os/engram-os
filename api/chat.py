import hashlib
import json
import logging
from typing import Generator

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from qdrant_client.http import models

from agents.logger import log_agent_action
from api.matters import _resolve_matter
from core.auth import get_current_user
from core.classification_engine import classify, Classification
from core.deps import COLLECTION_NAME, client, get_embedding, llm, LLM_MODEL
from core.sanitizer import sanitize
from core.schemas import ChatResponse, UserInput
from core.user_registry import User

logger = logging.getLogger(__name__)
router = APIRouter()

MAX_CONTEXT_CHARS = 4000


def _sse(data: dict) -> str:
    return f"data: {json.dumps(data)}\n\n"


def _build_context(item: UserInput, current_user, resolved_matter):
    """Shared retrieval + sanitization logic for both streaming and non-streaming paths."""
    query_vector = get_embedding(item.text)
    if not query_vector:
        return None, None, None, None

    try:
        must = [models.FieldCondition(key="user_id", match=models.MatchValue(value=current_user.id))]
        if resolved_matter is not None:
            must.append(models.FieldCondition(
                key="matter_id", match=models.MatchValue(value=resolved_matter)
            ))
        search_response = client.search(
            collection_name=COLLECTION_NAME,
            query_vector=query_vector,
            query_filter=models.Filter(must=must),
            limit=10,
            score_threshold=0.45,
        )
        search_hits = search_response.points
    except Exception as e:
        logger.error(f"Search failed: {e}")
        return None, None, None, None

    simple_sources = []
    lines = []
    for hit in search_hits:
        mem_text = hit.payload.get("memory") or "Unknown info"
        mem_classification = Classification[hit.payload.get("classification", "PUBLIC")]
        sanitized_mem = sanitize(mem_text, mem_classification)
        lines.append(f"- {sanitized_mem.text}")
        simple_sources.append({
            "memory": mem_text,
            "score": round(hit.score, 3),
            "classification": hit.payload.get("classification", "PUBLIC"),
        })
    context_str = "\n".join(lines)[:MAX_CONTEXT_CHARS]

    query_classification = classify(item.text)
    sanitized_query = sanitize(item.text, query_classification)

    if context_str.strip():
        system_prompt = (
            "You are a helpful Personal OS with access to the user's stored memories.\n"
            "Answer the user's question using ONLY the memories provided below.\n"
            "If the memories don't contain enough information to answer, say "
            "\"I don't have enough context stored about that yet.\"\n"
            "Do not invent, infer, or add information beyond what is in the memories.\n\n"
            "Stored memories:\n" + context_str
        )
    else:
        system_prompt = (
            "You are a helpful Personal OS.\n"
            "You have no stored memories relevant to this question.\n"
            "Respond with: \"I don't have anything stored about that yet.\"\n"
            "Do not make up or infer any information."
        )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": sanitized_query.text},
    ]
    return messages, simple_sources, search_hits, item.model or LLM_MODEL


def _stream_generator(
    messages: list[dict],
    model: str,
    sources: list,
    user_id: str,
    query_text: str,
    point_ids: str,
) -> Generator[str, None, None]:
    try:
        for token in llm.stream_chat(messages, model=model):
            yield _sse({"delta": token, "done": False})
    except Exception as e:
        logger.error(f"Stream generation failed: {e}")
    finally:
        log_agent_action(
            f"user:{user_id}", "READ",
            f"query_hash={hashlib.sha256(query_text.encode()).hexdigest()}",
            resource_id=point_ids,
        )
        yield _sse({"delta": "", "done": True, "context_used": sources})


@router.post("/chat")
def chat_with_memory(item: UserInput, current_user: User = Depends(get_current_user)):
    resolved_matter = _resolve_matter(current_user, item.matter_id)

    messages, sources, search_hits, model = _build_context(item, current_user, resolved_matter)

    if messages is None:
        if item.stream:
            def _error_stream():
                yield _sse({"delta": "Embedding Error", "done": False})
                yield _sse({"delta": "", "done": True, "context_used": []})
            return StreamingResponse(_error_stream(), media_type="text/event-stream",
                                     headers={"X-Accel-Buffering": "no", "Cache-Control": "no-cache"})
        return {"reply": "Embedding Error", "context_used": []}

    point_ids = ",".join(str(h.id) for h in search_hits)

    if item.stream:
        return StreamingResponse(
            _stream_generator(messages, model, sources, current_user.id, item.text, point_ids),
            media_type="text/event-stream",
            headers={"X-Accel-Buffering": "no", "Cache-Control": "no-cache"},
        )

    # Non-streaming path — unchanged behaviour.
    from fastapi import HTTPException
    ai_reply = llm.chat(messages=messages, model=model)
    if ai_reply is None:
        raise HTTPException(status_code=500, detail="LLM inference failed.")

    query_hash = hashlib.sha256(item.text.encode()).hexdigest()
    log_agent_action(
        f"user:{current_user.id}", "READ", f"query_hash={query_hash}",
        resource_id=point_ids,
    )
    return {"reply": ai_reply, "context_used": sources}
