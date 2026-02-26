import os
import asyncio
import logging
import requests
import uuid
from datetime import datetime
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
from mem0 import Memory
from qdrant_client import QdrantClient
from qdrant_client.http import models
from fastapi.middleware.cors import CORSMiddleware
import hashlib
import sys

from agents.tasks import run_calendar_agent, run_email_agent, test_agent_pulse
from ollama import Client as OllamaClient

from agents.terminal import router as terminal_router
from agents.spectre import router as spectre_router
from agents.git_automator import router as git_router

from core.identity import get_or_create_identity

from tools.visualizer import router as visualizer_router
from tools.crawler import DocSpider, collection 
from tools.pm_tools import IntegrationManager

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

IDENTITY = get_or_create_identity()
LOCAL_USER_ID = IDENTITY["user_id"]

app = FastAPI(title="Engram OS Brain")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(terminal_router)
app.include_router(spectre_router)
app.include_router(visualizer_router)
app.include_router(git_router)

OLLAMA_URL = os.getenv("OLLAMA_HOST", "http://host.docker.internal:11434")
QDRANT_HOST = os.getenv("QDRANT_HOST", "qdrant")
COLLECTION_NAME = "second_brain"
MAX_CONTEXT_CHARS = 4000

ollama_client = OllamaClient(host=OLLAMA_URL)
integration_manager = IntegrationManager()

config = {
    "vector_store": {
        "provider": "qdrant",
        "config": {
            "host": QDRANT_HOST,
            "port": 6333,
            "collection_name": COLLECTION_NAME,
            "embedding_model_dims": 768, 
        }
    },
    "llm": {
        "provider": "ollama",
        "config": {
            "model": "llama3.1:latest",
            "ollama_base_url": OLLAMA_URL,
            "temperature": 0
        }
    },
    "embedder": {
        "provider": "ollama",
        "config": {
            "model": "nomic-embed-text:latest",
            "ollama_base_url": OLLAMA_URL
        }
    }
}

m = Memory.from_config(config)
client = QdrantClient(host=QDRANT_HOST, port=6333)

class UserInput(BaseModel):
    text: str
    embed_text: str | None = None

class CrawlRequest(BaseModel):
    url: str
    max_pages: int = 10    

class QueryRequest(BaseModel):
    query: str

def get_embedding(text):
    try:
        res = requests.post(f"{OLLAMA_URL}/api/embeddings", json={
            "model": "nomic-embed-text:latest",
            "prompt": text
        }, timeout=30)
        return res.json()["embedding"]
    except Exception as e:
        logger.error(f"Embedding failed: {e}")
        return []

@app.get("/")
def read_root():
    return {"status": "Engram is Online", "version": "1.0.0"}

@app.get("/api/integrations/briefing")
def daily_briefing():
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
async def ingest_docs(request: CrawlRequest):
    spider = DocSpider(request.url, max_pages=request.max_pages)
    await asyncio.to_thread(spider.crawl)
    return {"status": "success", "message": f"Ingested {request.url}"}

@app.post("/api/docs/query")
def query_docs(request: QueryRequest):
    results = collection.query(query_texts=[request.query], n_results=3)
    context_parts = []
    sources = []

    if results['documents']:
        for i, doc in enumerate(results['documents'][0]):
            meta = results['metadatas'][0][i]
            context_parts.append(f"\n--- Source: {meta['source']} ---\n{doc}\n")
            sources.append(meta['source'])
    context = "".join(context_parts)

    prompt = f"Answer strictly using context:\n{context}\nQUESTION: {request.query}"
    response = ollama_client.chat(model='llama3.1:latest', messages=[{'role': 'user', 'content': prompt}])

    return {"answer": response['message']['content'], "sources": list(set(sources))}

@app.post("/trigger-agent")
async def trigger_agent_test():
    task = test_agent_pulse.delay("Hello from API") 
    return {"message": "Agent triggered", "task_id": task.id}

@app.post("/run-agents/calendar")
async def trigger_calendar_check():
    task = run_calendar_agent.delay()
    return {"message": "Calendar Agent activated", "task_id": task.id}

@app.post("/run-agents/email")
async def trigger_email_check():
    task = run_email_agent.delay()
    return {"message": "Email Agent activated", "task_id": task.id}

@app.post("/add-memory")
def add_memory(item: UserInput):
    m.add(item.text, user_id=LOCAL_USER_ID)
    return {"status": "profile_updated"}

@app.post("/ingest")
def ingest_file(item: UserInput):

    text_to_embed = item.embed_text if item.embed_text is not None else item.text

    vector = get_embedding(text_to_embed)
    if not vector: 
        raise HTTPException(status_code=500, detail="Embedding failed")

    content_type = getattr(item, "type", "raw_ingestion")
    
    similar = client.query_points(
        collection_name=COLLECTION_NAME, 
        query=vector, 
        query_filter=models.Filter(
        must=[
            models.FieldCondition(
                key="user_id", 
                match=models.MatchValue(value=LOCAL_USER_ID)
            ),
            models.FieldCondition(
                key="type", 
                match=models.MatchValue(value=content_type)
            )
        ]
    ), 
    limit=1, 
    score_threshold=0.97
    )
    if similar.points:
        return {
            "status": "duplicate_skipped", 
            "id": similar.points[0].id,
            "score": similar.points[0].score
            }

    content_hash = hashlib.sha256(
        f"{LOCAL_USER_ID}:{text_to_embed}".encode()
    ).hexdigest()
    point_id = str(uuid.UUID(content_hash[:32]))

    client.upsert(
        collection_name=COLLECTION_NAME,
        points=[models.PointStruct(
            id=point_id, 
            vector=vector, 
            payload={
                "memory": item.text, 
                "embed_text": text_to_embed,
                "user_id": LOCAL_USER_ID,
                "type": content_type, 
                "created_at": str(datetime.now())
            }
        )]
    )
    return {"status": "raw_data_saved", "id": point_id}

@app.get("/search")
def search_memory(query: str):
    return {"results": m.search(query, user_id=LOCAL_USER_ID)}

@app.get("/api/search/unified")
def unified_search(query: str, n_results: int = 5):
    results = []

    # 1. Qdrant — personal memories
    query_vector = get_embedding(query)
    if query_vector:
        try:
            hits = client.query_points(
                collection_name=COLLECTION_NAME,
                query=query_vector,
                query_filter=models.Filter(must=[
                    models.FieldCondition(key="user_id", match=models.MatchValue(value=LOCAL_USER_ID))
                ]),
                limit=n_results,
                score_threshold=0.45
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

@app.post("/chat")
def chat_with_memory(item: UserInput):
    query_vector = get_embedding(item.text)
    if query_vector is None:
        return {"reply": "Embedding Error", "context_used": []}

    try:
        search_response = client.query_points(
            collection_name=COLLECTION_NAME, 
            query=query_vector, 
            query_filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="user_id",
                        match=models.MatchValue(value=LOCAL_USER_ID)
                    )
                ]
            ),
            limit=5,
            score_threshold=0.45
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
        lines.append(f"- {mem_text}")
        simple_sources.append({
            "memory": mem_text,
            "score": round(hit.score, 3)
        })
    context_str = "\n".join(lines)[:MAX_CONTEXT_CHARS]

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
        ollama_res = requests.post(
            f"{OLLAMA_URL}/api/chat",
            json={
                "model": "llama3.1:latest",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": item.text}
                ],
                "stream": False
            },
            timeout=60
        )
        ai_reply = ollama_res.json().get("message", {}).get("content", "Error.")
        return {"reply": ai_reply, "context_used": simple_sources}
    except Exception as e:
        logger.error(f"Generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))