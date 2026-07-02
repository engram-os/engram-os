import hashlib
import logging
import os
import uuid
from datetime import datetime

from mcp.server.fastmcp import FastMCP
from qdrant_client.http import models

from core.classification_engine import classify
from core.deps import COLLECTION_NAME, client, get_embedding
from core.matter_registry import list_matters_for_user

logger = logging.getLogger(__name__)

USER_ID: str = os.getenv("ENGRAM_USER_ID", "")

mcp = FastMCP("Engram")


@mcp.tool()
def memory_search(query: str, matter_id: str | None = None) -> list[dict]:
    """Search your stored memories semantically. Returns relevant memories with scores."""
    vector = get_embedding(query)
    if not vector:
        return []

    must = [models.FieldCondition(key="user_id", match=models.MatchValue(value=USER_ID))]
    if matter_id:
        must.append(models.FieldCondition(key="matter_id", match=models.MatchValue(value=matter_id)))

    result = client.search(
        collection_name=COLLECTION_NAME,
        query_vector=vector,
        query_filter=models.Filter(must=must),
        limit=10,
        score_threshold=0.45,
    )
    return [
        {
            "memory": hit.payload.get("memory", ""),
            "score": round(hit.score, 3),
            "matter_id": hit.payload.get("matter_id", ""),
            "classification": hit.payload.get("classification", "PUBLIC"),
        }
        for hit in result.points
    ]


@mcp.tool()
def memory_ingest(text: str, type: str = "explicit_memory", matter_id: str | None = None) -> dict:
    """Store a new memory. Returns the stored memory's ID."""
    vector = get_embedding(text)
    if not vector:
        return {"status": "error", "reason": "embedding failed"}

    content_hash = hashlib.sha256(f"{USER_ID}:{text}".encode()).hexdigest()
    point_id = str(uuid.UUID(content_hash[:32]))
    data_classification = classify(text)

    client.write(
        collection_name=COLLECTION_NAME,
        point_id=point_id,
        vector=vector,
        payload={
            "memory": text,
            "user_id": USER_ID,
            "matter_id": matter_id or "",
            "type": type,
            "created_at": str(datetime.now()),
        },
        classification=data_classification.name,
    )
    return {"status": "stored", "id": point_id}


@mcp.tool()
def memory_matters() -> list[dict]:
    """List all matters (cases, projects, contexts) available to you."""
    matters = list_matters_for_user(USER_ID)
    return [{"id": m["id"], "name": m["name"]} for m in matters]


@mcp.resource("memory://{matter_id}")
def memory_resource(matter_id: str) -> str:
    """Browse all memories stored in a specific matter."""
    must = [
        models.FieldCondition(key="user_id", match=models.MatchValue(value=USER_ID)),
        models.FieldCondition(key="matter_id", match=models.MatchValue(value=matter_id)),
    ]
    points, _ = client.scroll(
        collection_name=COLLECTION_NAME,
        scroll_filter=models.Filter(must=must),
        limit=50,
    )
    if not points:
        return f"No memories found in matter {matter_id}."
    lines = [
        f"[{p.payload.get('classification', 'PUBLIC')}] {p.payload.get('memory', '')}"
        for p in points
    ]
    return "\n".join(lines)
