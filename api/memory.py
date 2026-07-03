import hashlib
import logging
import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from qdrant_client.http import models

from agents.logger import log_agent_action
from api.matters import _resolve_matter
from core.auth import get_current_user
from core.classification_engine import classify
from core.deps import COLLECTION_NAME, client, get_embedding
from core.schemas import IngestResponse, UserInput, _VALID_CONTENT_TYPES
from core.user_registry import User

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/api/memories")
def list_memories(
    matter_id: str | None = Query(default=None, max_length=100),
    type: Optional[_VALID_CONTENT_TYPES] = Query(default=None),
    classification: str | None = Query(default=None, max_length=50),
    limit: int = Query(default=20, ge=1, le=100),
    offset: str | None = Query(default=None),
    current_user: User = Depends(get_current_user),
):
    """Scroll through stored memories with optional filters. Pagination via next_offset."""
    must = [models.FieldCondition(key="user_id", match=models.MatchValue(value=current_user.id))]
    if matter_id:
        must.append(models.FieldCondition(key="matter_id", match=models.MatchValue(value=matter_id)))
    if type:
        must.append(models.FieldCondition(key="type", match=models.MatchValue(value=type)))
    if classification:
        must.append(models.FieldCondition(key="classification", match=models.MatchValue(value=classification)))

    points, next_offset = client.scroll(
        collection_name=COLLECTION_NAME,
        scroll_filter=models.Filter(must=must),
        limit=limit,
        offset=offset,
    )

    return {
        "memories": [
            {
                "id": str(p.id),
                "memory": p.payload.get("memory", ""),
                "type": p.payload.get("type", ""),
                "matter_id": p.payload.get("matter_id", ""),
                "classification": p.payload.get("classification", "PUBLIC"),
                "created_at": p.payload.get("created_at", ""),
            }
            for p in points
        ],
        "next_offset": str(next_offset) if next_offset else None,
    }


@router.post("/add-memory")
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


@router.post("/ingest", response_model=IngestResponse)
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

    # Composite key hash for structured docs; content hash fallback for unstructured.
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


@router.delete("/api/memory/{point_id}")
def delete_memory_by_id(
    point_id: str,
    current_user: User = Depends(get_current_user),
):
    """Delete a single memory point by ID. Caller must own the point."""
    import json
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


@router.delete("/api/memories")
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


@router.get("/search")
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


@router.get("/api/search/unified")
def unified_search(
    query: str = Query(..., min_length=1, max_length=1_000),
    n_results: int = Query(default=5, ge=1, le=50),
    matter_id: str | None = Query(default=None, max_length=100),
    current_user: User = Depends(get_current_user),
):
    resolved_matter = _resolve_matter(current_user, matter_id)
    results = []

    query_vector = get_embedding(query)
    if query_vector:
        try:
            must = [models.FieldCondition(key="user_id", match=models.MatchValue(value=current_user.id))]
            if resolved_matter is not None:
                must.append(models.FieldCondition(
                    key="matter_id", match=models.MatchValue(value=resolved_matter)
                ))
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

        try:
            doc_hits = client._qdrant.query_points(
                collection_name="doc_knowledge",
                query=query_vector,
                limit=n_results,
                score_threshold=0.3,
            )
            for hit in doc_hits.points:
                results.append({
                    "source": "doc_knowledge",
                    "content": hit.payload.get("content", ""),
                    "score": round(hit.score, 3),
                    "metadata": {
                        "source": hit.payload.get("source", ""),
                        "type": hit.payload.get("type", ""),
                    },
                })
        except Exception as e:
            logger.error(f"Doc knowledge unified search failed: {e}")

    return {"query": query, "results": results, "total": len(results)}
