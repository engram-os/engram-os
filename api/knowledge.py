import asyncio
import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from core.auth import get_current_user
from core.deps import client, get_embedding, llm
from core.network_gateway import gateway, is_safe_url
from core.user_registry import User
from tools.crawler import DocSpider

logger = logging.getLogger(__name__)
router = APIRouter()


class CrawlRequest(BaseModel):
    url: str = Field(..., min_length=1, max_length=2_048)
    max_pages: int = Field(default=10, ge=1, le=100)


class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=1_000)


@router.get("/api/models")
def list_models(_: User = Depends(get_current_user)):
    try:
        res = gateway.get("ollama", "/api/tags", timeout=5)
        return res.json()
    except Exception:
        return {"models": []}


@router.post("/api/docs/ingest")
async def ingest_docs(request: CrawlRequest, current_user: User = Depends(get_current_user)):
    if not is_safe_url(request.url):
        raise HTTPException(status_code=400, detail="URL targets a blocked or private network resource.")
    spider = DocSpider(request.url, max_pages=request.max_pages)
    await asyncio.to_thread(spider.crawl)
    return {"status": "success", "message": f"Ingested {request.url}"}


@router.post("/api/docs/query")
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
                context_parts.append(
                    f"\n--- Source: {hit.payload.get('source', '')} ---\n{hit.payload.get('content', '')}\n"
                )
                sources.append(hit.payload.get("source", ""))
        except Exception as e:
            logger.error(f"Doc query failed: {e}")

    context = "".join(context_parts)
    prompt = f"Answer strictly using context:\n{context}\nQUESTION: {request.query}"
    answer = llm.chat([{"role": "user", "content": prompt}])
    return {"answer": answer or "Error generating answer.", "sources": list(set(sources))}
