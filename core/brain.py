import os
import asyncio
import logging
from core.network_gateway import gateway
import uuid
from datetime import datetime
from fastapi import FastAPI, HTTPException, Query, Security, Depends
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, Field
from typing import Optional, Literal
from qdrant_client import QdrantClient
from qdrant_client.http import models
from fastapi.middleware.cors import CORSMiddleware
import hashlib
import json
import sys

from agents.tasks import run_calendar_agent, run_email_agent, test_agent_pulse
from agents.logger import verify_audit_chain, log_agent_action, get_recent_logs
from core.schemas import ChatResponse, IngestResponse, AuditVerifyResponse
from ollama import Client as OllamaClient

from agents.terminal import router as terminal_router
from agents.spectre import router as spectre_router
from agents.git_automator import router as git_router

from core.identity import get_or_create_identity
from core.memory_client import EncryptedMemoryClient, load_encryption_key
from core.classification_engine import classify, Classification
from core.sanitizer import sanitize
from core.user_registry import (
    bootstrap_admin, get_user_by_key, create_user, list_users, User,
)
from core.matter_registry import (
    bootstrap_default_matter, get_matter, list_matters_for_user,
    check_access, grant_access, create_matter as registry_create_matter,
    close_matter as registry_close_matter,
)

from tools.crawler import DocSpider
from core.network_gateway import is_safe_url
from tools.pm_tools import IntegrationManager

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

IDENTITY = get_or_create_identity()
LOCAL_USER_ID = IDENTITY["user_id"]

app = FastAPI(title="Engram OS Brain")

ALLOWED_ORIGINS = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:8501,http://127.0.0.1:8501,http://localhost:3000,http://127.0.0.1:3000"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(terminal_router)
app.include_router(spectre_router)
app.include_router(git_router)

OLLAMA_URL = os.getenv("OLLAMA_HOST", "http://host.docker.internal:11434")
QDRANT_HOST = os.getenv("QDRANT_HOST", "qdrant")

# API key auth — only enforced when ENGRAM_API_KEY is set in the environment.
# When unset (dev mode), all requests receive a synthetic admin identity
# backed by LOCAL_USER_ID — zero behaviour change for single-user deployments.
_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
_ENGRAM_API_KEY = os.getenv("ENGRAM_API_KEY")


def get_current_user(raw_key: str | None = Security(_api_key_header)) -> User:
    if not _ENGRAM_API_KEY:
        # Dev mode: no auth enforced — synthetic admin using machine identity.
        return User(id=LOCAL_USER_ID, role="admin", display_name="local-admin")
    if not raw_key:
        raise HTTPException(status_code=403, detail="X-API-Key header required.")
    user = get_user_by_key(raw_key)
    if not user:
        raise HTTPException(status_code=403, detail="Invalid API key.")
    return user


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required.")
    return current_user


# Seed the user registry and default matter on startup (idempotent).
if _ENGRAM_API_KEY:
    bootstrap_admin(LOCAL_USER_ID, _ENGRAM_API_KEY)
    bootstrap_default_matter(LOCAL_USER_ID)
COLLECTION_NAME = "second_brain"
MAX_CONTEXT_CHARS = 4000

ollama_client = OllamaClient(host=OLLAMA_URL)
integration_manager = IntegrationManager()

client = EncryptedMemoryClient(
    QdrantClient(host=QDRANT_HOST, port=6333),
    load_encryption_key(),
)

_VALID_CONTENT_TYPES = Literal["raw_ingestion", "browsing_event", "file_ingest", "explicit_memory"]

class UserInput(BaseModel):
    text: str = Field(..., min_length=1, max_length=50_000)
    embed_text: str | None = Field(default=None, max_length=50_000)
    type: _VALID_CONTENT_TYPES = Field(default="raw_ingestion")
    matter_id: str | None = Field(default=None, max_length=100)
    document_keys: dict | None = Field(default=None)
    created_at: str | None = Field(default=None)


def _resolve_matter(user: User, matter_id: str | None) -> str | None:
    """Validate matter access and return the resolved matter_id.

    Returns None when matter_id is None — this means 'no filter', preserving
    full backwards compatibility with untagged legacy data.
    """
    if matter_id is None:
        return None
    matter = get_matter(matter_id)
    if not matter:
        raise HTTPException(status_code=404, detail=f"Matter '{matter_id}' not found.")
    if matter["status"] == "closed":
        raise HTTPException(status_code=410, detail=f"Matter '{matter_id}' is closed.")
    # Admins bypass the access check; regular users must be granted access.
    if user.role != "admin" and not check_access(user.id, matter_id):
        raise HTTPException(status_code=403, detail="Access denied to this matter.")
    return matter_id

class CrawlRequest(BaseModel):
    url: str = Field(..., min_length=1, max_length=2_048)
    max_pages: int = Field(default=10, ge=1, le=100)

class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=1_000)

def get_embedding(text) -> list[float] | None:
    try:
        res = gateway.post("ollama", "/api/embeddings", json={
            "model": "nomic-embed-text:latest",
            "prompt": text
        }, timeout=30)
        return res.json()["embedding"]
    except Exception as e:
        logger.error(f"Embedding failed: {e}")
        return None

@app.get("/")
def read_root():
    return {"status": "Engram is Online", "version": "1.0.0"}


@app.get("/api/audit/verify", response_model=AuditVerifyResponse)
def audit_verify(current_user: User = Depends(require_admin)):
    """Walk the full audit log and verify every HMAC chain link is unbroken."""
    return verify_audit_chain()


@app.get("/api/audit/logs")
def audit_logs(
    limit: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(require_admin),
):
    """Return the most recent audit log entries (newest first)."""
    rows = get_recent_logs(limit)
    return {
        "logs": [
            {"timestamp": r[0], "actor": r[1], "action": r[2], "details": r[3]}
            for r in rows
        ]
    }


# ─── User management endpoints ────────────────────────────────────────────────

@app.get("/api/me")
def get_me(current_user: User = Depends(get_current_user)):
    return {"id": current_user.id, "role": current_user.role, "display_name": current_user.display_name}


@app.post("/api/users")
def create_new_user(
    display_name: str = Query(..., min_length=1, max_length=100),
    role: str = Query(default="user"),
    _admin: User = Depends(require_admin),
):
    if role not in ("admin", "user"):
        raise HTTPException(status_code=422, detail="role must be 'admin' or 'user'.")
    user_id, raw_key = create_user(display_name=display_name, role=role)
    return {"user_id": user_id, "api_key": raw_key, "display_name": display_name}


@app.get("/api/users")
def list_all_users(_admin: User = Depends(require_admin)):
    return {"users": list_users()}


# ─── Matter management endpoints ─────────────────────────────────────────────

@app.get("/api/matters")
def get_matters(current_user: User = Depends(get_current_user)):
    return {"matters": list_matters_for_user(current_user.id)}


@app.post("/api/matters")
def new_matter(
    name: str = Query(..., min_length=1, max_length=200),
    current_user: User = Depends(get_current_user),
):
    matter_id = registry_create_matter(name=name, created_by=current_user.id)
    return {"matter_id": matter_id, "name": name}


@app.post("/api/matters/{matter_id}/close")
def close_matter_endpoint(matter_id: str, current_user: User = Depends(get_current_user)):
    matter = get_matter(matter_id)
    if not matter:
        raise HTTPException(status_code=404, detail=f"Matter '{matter_id}' not found.")
    if matter["status"] == "closed":
        raise HTTPException(status_code=410, detail=f"Matter '{matter_id}' is already closed.")
    # Only the creator or an admin can close a matter.
    if current_user.role != "admin" and matter["created_by"] != current_user.id:
        raise HTTPException(status_code=403, detail="Only the matter owner or an admin can close it.")

    # Scroll and batch-delete all Qdrant points for this matter.
    deleted_count = 0
    offset = None
    while True:
        batch, next_offset = client.scroll(
            collection_name=COLLECTION_NAME,
            scroll_filter=models.Filter(must=[
                models.FieldCondition(key="matter_id", match=models.MatchValue(value=matter_id)),
            ]),
            limit=100,
            offset=offset,
            with_payload=False,
        )
        if not batch:
            break
        ids = [p.id for p in batch]
        client.delete(
            collection_name=COLLECTION_NAME,
            points_selector=models.PointIdsList(points=ids),
        )
        deleted_count += len(ids)
        offset = next_offset
        if not next_offset:
            break

    registry_close_matter(matter_id, closed_by=current_user.id)
    log_agent_action(
        f"user:{current_user.id}", "DELETE",
        f"matter_closed:{matter_id}:{deleted_count}_points",
        resource_id=matter_id,
    )
    return {"matter_id": matter_id, "deleted_points": deleted_count}


@app.post("/api/matters/{matter_id}/access")
def grant_matter_access(
    matter_id: str,
    user_id: str = Query(..., min_length=1, max_length=100),
    _admin: User = Depends(require_admin),
):
    matter = get_matter(matter_id)
    if not matter:
        raise HTTPException(status_code=404, detail=f"Matter '{matter_id}' not found.")
    grant_access(matter_id=matter_id, user_id=user_id, granted_by=_admin.id)
    return {"status": "access_granted", "matter_id": matter_id, "user_id": user_id}


@app.get("/api/integrations/briefing")
def daily_briefing(current_user: User = Depends(get_current_user)):
    tasks = integration_manager.get_combined_briefing_data()
    
    if not tasks:
        return {"briefing": "No active tasks in Jira/Linear.", "tasks": []}

    task_list_str = "\n".join([f"- [{t.source}] {t.priority}: {t.title} ({t.status})" for t in tasks])
    
    prompt = f"""
    You are an executive assistant. Here are the user's active tasks for today:
    {task_list_str}
    Write a concise "Daily Briefing" paragraph (max 3 sentences). 
    """
    
    response = ollama_client.chat(model='llama3.1:latest', messages=[{'role': 'user', 'content': prompt}])
    return {"briefing": response['message']['content'], "tasks": tasks}

@app.post("/api/docs/ingest")
async def ingest_docs(request: CrawlRequest, current_user: User = Depends(get_current_user)):
    if not is_safe_url(request.url):
        raise HTTPException(status_code=400, detail="URL targets a blocked or private network resource.")
    spider = DocSpider(request.url, max_pages=request.max_pages)
    await asyncio.to_thread(spider.crawl)
    return {"status": "success", "message": f"Ingested {request.url}"}

@app.post("/api/docs/query")
def query_docs(request: QueryRequest, current_user: User = Depends(get_current_user)):
    query_vector = get_embedding(request.query)
    context_parts = []
    sources = []

    if query_vector:
        try:
            hits = client._qdrant.query_points(
                collection_name="doc_knowledge",
                query=query_vector,
                limit=3,
                score_threshold=0.3,
            )
            for hit in hits.points:
                context_parts.append(f"\n--- Source: {hit.payload.get('source', '')} ---\n{hit.payload.get('content', '')}\n")
                sources.append(hit.payload.get('source', ''))
        except Exception as e:
            logger.error(f"Doc query failed: {e}")

    context = "".join(context_parts)
    prompt = f"Answer strictly using context:\n{context}\nQUESTION: {request.query}"
    response = ollama_client.chat(model='llama3.1:latest', messages=[{'role': 'user', 'content': prompt}])

    return {"answer": response['message']['content'], "sources": list(set(sources))}

@app.post("/trigger-agent")
async def trigger_agent_test(current_user: User = Depends(get_current_user)):
    task = test_agent_pulse.delay("Hello from API")
    return {"message": "Agent triggered", "task_id": task.id}

@app.post("/run-agents/calendar")
async def trigger_calendar_check(current_user: User = Depends(get_current_user)):
    task = run_calendar_agent.delay(user_id=current_user.id)
    return {"message": "Calendar Agent activated", "task_id": task.id, "user_id": current_user.id}

@app.post("/run-agents/email")
async def trigger_email_check(current_user: User = Depends(get_current_user)):
    task = run_email_agent.delay(user_id=current_user.id)
    return {"message": "Email Agent activated", "task_id": task.id, "user_id": current_user.id}

@app.post("/add-memory")
def add_memory(item: UserInput, current_user: User = Depends(get_current_user)):
    resolved_matter = _resolve_matter(current_user, item.matter_id)

    vector = get_embedding(item.text)
    if not vector:
        raise HTTPException(status_code=500, detail="Embedding failed")

    must = [
        models.FieldCondition(key="user_id", match=models.MatchValue(value=current_user.id)),
        models.FieldCondition(key="type", match=models.MatchValue(value="explicit_memory")),
    ]
    if resolved_matter is not None:
        must.append(models.FieldCondition(key="matter_id", match=models.MatchValue(value=resolved_matter)))

    similar = client.search(
        collection_name=COLLECTION_NAME,
        query_vector=vector,
        query_filter=models.Filter(must=must),
        limit=1,
        score_threshold=0.97,
    )
    if similar.points:
        return {"status": "duplicate_skipped", "id": similar.points[0].id}

    content_hash = hashlib.sha256(f"{current_user.id}:{item.text}".encode()).hexdigest()
    point_id = str(uuid.UUID(content_hash[:32]))

    data_classification = classify(item.text)
    client.write(
        collection_name=COLLECTION_NAME,
        point_id=point_id,
        vector=vector,
        payload={
            "memory": item.text,
            "user_id": current_user.id,
            "matter_id": resolved_matter or "",
            "type": "explicit_memory",
            "created_at": item.created_at or str(datetime.now()),
        },
        classification=data_classification.name,
    )
    log_agent_action(f"user:{current_user.id}", "WRITE", "explicit_memory", resource_id=point_id)
    return {"status": "memory_saved", "id": point_id}

@app.post("/ingest", response_model=IngestResponse)
def ingest_file(item: UserInput, current_user: User = Depends(get_current_user)):
    resolved_matter = _resolve_matter(current_user, item.matter_id)

    text_to_embed = item.embed_text if item.embed_text is not None else item.text
    vector = get_embedding(text_to_embed)
    if not vector:
        raise HTTPException(status_code=500, detail="Embedding failed")

    content_type = item.type

    must = [
        models.FieldCondition(key="user_id", match=models.MatchValue(value=current_user.id)),
        models.FieldCondition(key="type", match=models.MatchValue(value=content_type)),
    ]
    if resolved_matter is not None:
        must.append(models.FieldCondition(key="matter_id", match=models.MatchValue(value=resolved_matter)))

    # Explicit file drops are always intentional — skip semantic dedup.
    # Sensor data (raw_ingestion, browsing_event) still uses similarity dedup.
    if content_type != "file_ingest":
        similar = client.search(
            collection_name=COLLECTION_NAME,
            query_vector=vector,
            query_filter=models.Filter(must=must),
            limit=1,
            score_threshold=0.97,
        )
        if similar.points:
            return {
                "status": "duplicate_skipped",
                "id": similar.points[0].id,
                "score": similar.points[0].score,
            }

    # Use composite key hash when structured keys were extracted (file_ingest),
    # falling back to content hash for unstructured files or sensor data.
    doc_keys = item.document_keys or {}
    primary_id = doc_keys.get("claim_number") or doc_keys.get("auth_number") or doc_keys.get("reference")
    id_source = f"{current_user.id}:{primary_id}" if primary_id else f"{current_user.id}:{text_to_embed}"
    content_hash = hashlib.sha256(id_source.encode()).hexdigest()
    point_id = str(uuid.UUID(content_hash[:32]))

    data_classification = classify(item.text)
    client.write(
        collection_name=COLLECTION_NAME,
        point_id=point_id,
        vector=vector,
        payload={
            "memory": item.text,
            "embed_text": text_to_embed,
            "user_id": current_user.id,
            "matter_id": resolved_matter or "",
            "type": content_type,
            "created_at": item.created_at or str(datetime.now()),
            **doc_keys,
        },
        classification=data_classification.name,
    )
    log_agent_action(f"user:{current_user.id}", "WRITE", f"type={content_type}", resource_id=point_id)
    return {"status": "raw_data_saved", "id": point_id}


# ─── Memory deletion endpoints ────────────────────────────────────────────────

@app.delete("/api/memory/{point_id}")
def delete_memory_by_id(
    point_id: str,
    current_user: User = Depends(get_current_user),
):
    """Delete a single memory point by ID. Caller must own the point."""
    try:
        uuid.UUID(point_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid point_id: must be a valid UUID.")

    try:
        points = client._qdrant.retrieve(
            collection_name=COLLECTION_NAME,
            ids=[point_id],
            with_payload=True,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Retrieval failed: {e}")

    if not points:
        raise HTTPException(status_code=404, detail="Memory not found.")

    payload = points[0].payload or {}
    if payload.get("user_id") != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied.")

    client.delete(
        collection_name=COLLECTION_NAME,
        points_selector=models.PointIdsList(points=[point_id]),
    )

    payload_hash = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
    log_agent_action(
        f"user:{current_user.id}", "DELETE", f"payload_hash:{payload_hash}",
        resource_id=point_id,
        matter_id=payload.get("matter_id", ""),
    )
    return {"status": "deleted", "id": point_id}


@app.delete("/api/memories")
def delete_memories_batch(
    matter_id: str = Query(..., min_length=1, max_length=100),
    type: Optional[_VALID_CONTENT_TYPES] = Query(default=None),
    current_user: User = Depends(get_current_user),
):
    """Batch-delete all memories for a matter, optionally filtered by type."""
    resolved_matter = _resolve_matter(current_user, matter_id)

    must = [
        models.FieldCondition(key="user_id", match=models.MatchValue(value=current_user.id)),
        models.FieldCondition(key="matter_id", match=models.MatchValue(value=resolved_matter)),
    ]
    if type is not None:
        must.append(models.FieldCondition(key="type", match=models.MatchValue(value=type)))

    client.delete(
        collection_name=COLLECTION_NAME,
        points_selector=models.FilterSelector(filter=models.Filter(must=must)),
    )

    log_agent_action(
        f"user:{current_user.id}", "DELETE_BATCH",
        f"matter_id={resolved_matter} type={type or 'all'}",
        resource_id=f"matter:{resolved_matter}",
        matter_id=resolved_matter or "",
    )
    return {"status": "deleted", "matter_id": resolved_matter, "type": type}


@app.get("/search")
def search_memory(
    query: str = Query(..., min_length=1, max_length=1_000),
    matter_id: str | None = Query(default=None, max_length=100),
    current_user: User = Depends(get_current_user),
):
    resolved_matter = _resolve_matter(current_user, matter_id)

    query_vector = get_embedding(query)
    if not query_vector:
        raise HTTPException(status_code=500, detail="Embedding failed")

    must = [models.FieldCondition(key="user_id", match=models.MatchValue(value=current_user.id))]
    if resolved_matter is not None:
        must.append(models.FieldCondition(key="matter_id", match=models.MatchValue(value=resolved_matter)))

    hits = client.search(
        collection_name=COLLECTION_NAME,
        query_vector=query_vector,
        query_filter=models.Filter(must=must),
        limit=10,
        score_threshold=0.45,
    )
    results = [
        {"memory": h.payload.get("memory", ""), "score": round(h.score, 3)}
        for h in hits.points
    ]
    query_hash = hashlib.sha256(query.encode()).hexdigest()
    log_agent_action(f"user:{current_user.id}", "READ", f"query_hash={query_hash}")
    return {"results": results}

@app.get("/api/search/unified")
def unified_search(
    query: str = Query(..., min_length=1, max_length=1_000),
    n_results: int = Query(default=5, ge=1, le=50),
    matter_id: str | None = Query(default=None, max_length=100),
    current_user: User = Depends(get_current_user),
):
    resolved_matter = _resolve_matter(current_user, matter_id)
    results = []

    # 1. Qdrant — personal memories
    query_vector = get_embedding(query)
    if query_vector:
        try:
            must = [models.FieldCondition(key="user_id", match=models.MatchValue(value=current_user.id))]
            if resolved_matter is not None:
                must.append(models.FieldCondition(key="matter_id", match=models.MatchValue(value=resolved_matter)))
            hits = client.search(
                collection_name=COLLECTION_NAME,
                query_vector=query_vector,
                query_filter=models.Filter(must=must),
                limit=n_results,
                score_threshold=0.45,
            )
            for hit in hits.points:
                results.append({
                    "source": "personal_memory",
                    "content": hit.payload.get("memory", ""),
                    "score": round(hit.score, 3),
                    "metadata": {}
                })
        except Exception as e:
            logger.error(f"Qdrant unified search failed: {e}")

    # 2. ChromaDB — doc knowledge
    try:
        chroma_res = collection.query(query_texts=[query], n_results=n_results)
        if chroma_res["documents"]:
            for i, doc in enumerate(chroma_res["documents"][0]):
                meta = chroma_res["metadatas"][0][i]
                distance = chroma_res["distances"][0][i]
                results.append({
                    "source": "doc_knowledge",
                    "content": doc,
                    "score": round(1 - distance, 3),
                    "metadata": meta
                })
    except Exception as e:
        logger.error(f"ChromaDB unified search failed: {e}")

    return {"query": query, "results": results, "total": len(results)}

@app.post("/chat", response_model=ChatResponse)
def chat_with_memory(item: UserInput, current_user: User = Depends(get_current_user)):
    resolved_matter = _resolve_matter(current_user, item.matter_id)

    query_vector = get_embedding(item.text)
    if not query_vector:
        return {"reply": "Embedding Error", "context_used": []}

    try:
        must = [models.FieldCondition(key="user_id", match=models.MatchValue(value=current_user.id))]
        if resolved_matter is not None:
            must.append(models.FieldCondition(key="matter_id", match=models.MatchValue(value=resolved_matter)))
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
        return {"reply": "Database Error", "context_used": []}
    
    simple_sources = []
    context_str = ""

    lines = []
    for hit in search_hits:
        mem_text = hit.payload.get('memory') or "Unknown info"
        # Sanitize each memory before it enters the LLM prompt.
        # classification is stored as plaintext in Qdrant (ARCH-1).
        mem_classification = Classification[hit.payload.get('classification', 'PUBLIC')]
        sanitized_mem = sanitize(mem_text, mem_classification)
        lines.append(f"- {sanitized_mem.text}")
        simple_sources.append({
            "memory": mem_text,  # return original to caller, not sanitized
            "score": round(hit.score, 3)
        })
    context_str = "\n".join(lines)[:MAX_CONTEXT_CHARS]

    # Sanitize the user's query before sending to Ollama.
    query_classification = classify(item.text)
    sanitized_query = sanitize(item.text, query_classification)

    if context_str.strip():
        system_prompt = """You are a helpful Personal OS with access to the user's stored memories.
        Answer the user's question using ONLY the memories provided below.
        If the memories don't contain enough information to answer, say "I don't have enough context stored about that yet."
        Do not invent, infer, or add information beyond what is in the memories.

    Stored memories:
    """ + context_str
    else:
        system_prompt = """You are a helpful Personal OS.
        You have no stored memories relevant to this question.
        Respond with: "I don't have anything stored about that yet."
        Do not make up or infer any information."""

    try:
        ollama_res = gateway.post(
            "ollama", "/api/chat",
            json={
                "model": "llama3.1:latest",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": sanitized_query.text}
                ],
                "stream": False
            },
            timeout=60
        )
        ai_reply = ollama_res.json().get("message", {}).get("content", "Error.")
        point_ids = ",".join(str(h.id) for h in search_hits)
        query_hash = hashlib.sha256(item.text.encode()).hexdigest()
        log_agent_action(
            f"user:{current_user.id}", "READ", f"query_hash={query_hash}",
            resource_id=point_ids,
        )
        return {"reply": ai_reply, "context_used": simple_sources}
    except Exception as e:
        logger.error(f"Generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))