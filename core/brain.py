import os
import logging
import requests
import uuid
import datetime
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from mem0 import Memory
from qdrant_client import QdrantClient
from qdrant_client.http import models
from fastapi.middleware.cors import CORSMiddleware
import hashlib

from agents.tasks import run_calendar_agent, run_email_agent, test_agent_pulse
from agents.terminal import router as terminal_router
from agents.spectre import router as spectre_router
from agents.git_automator import router as git_router
from agents.git_automator import client

from tools.visualizer import router as visualizer_router
from tools.crawler import DocSpider, collection 
from tools.pm_tools import IntegrationManager

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI(title="Engram OS Brain")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
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
    user_id: str = "default_user"

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
        })
        return res.json()["embedding"]
    except Exception as e:
        logger.error(f"Embedding failed: {e}")
        return []

@app.get("/")
def read_root():
    return {"status": "Engram is Online", "version": "1.0.0"}

@app.get("/api/integrations/briefing")
async def daily_briefing():
    manager = IntegrationManager()
    tasks = manager.get_combined_briefing_data()
    
    if not tasks:
        return {"briefing": "No active tasks in Jira/Linear.", "tasks": []}

    task_list_str = "\n".join([f"- [{t.source}] {t.priority}: {t.title} ({t.status})" for t in tasks])
    
    prompt = f"""
    You are an executive assistant. Here are the user's active tasks for today:
    {task_list_str}
    Write a concise "Daily Briefing" paragraph (max 3 sentences). 
    """
    
    response = client.chat(model='llama3', messages=[{'role': 'user', 'content': prompt}])
    return {"briefing": response['message']['content'], "tasks": tasks}    

@app.post("/api/docs/ingest")
async def ingest_docs(request: CrawlRequest):
    spider = DocSpider(request.url, max_pages=request.max_pages)
    spider.crawl() 
    return {"status": "success", "message": f"Ingested {request.url}"}

@app.post("/api/docs/query")
async def query_docs(request: QueryRequest):
    results = collection.query(query_texts=[request.query], n_results=3)
    context = ""
    sources = []
    
    if results['documents']:
        for i, doc in enumerate(results['documents'][0]):
            meta = results['metadatas'][0][i]
            context += f"\n--- Source: {meta['source']} ---\n{doc}\n"
            sources.append(meta['source'])

    prompt = f"Answer strictly using context:\n{context}\nQUESTION: {request.query}"
    response = client.chat(model='llama3.1:latest', messages=[{'role': 'user', 'content': prompt}])
    
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
    m.add(item.text, user_id=item.user_id)
    return {"status": "profile_updated"}

@app.post("/ingest")
def ingest_file(item: UserInput):

    text_to_embed = getattr(item, "embed-text", None) or item.text

    vector = get_embedding(text_to_embed)
    if not vector: 
        raise HTTPException(status_code=500, detail="Embedding failed")
    
    similar = client.query_points(
        collection_name=COLLECTION_NAME, 
        query=vector, 
        query_filter=models.Filter(
        must=[
            models.FieldCondition(
                key="user_id", 
                match=models.MatchValue(value=item.user_id)
            ),
            models.FieldCondition(
                key="type", 
                match=models.MatchValue(value="browsing_event")
            )
        ]
    ), 
    limit=1, 
    score_threshold=0.97
    )
    if similar.points:
        return {
            "status": "duplicate_skipped", 
            "id": similar[0].id
            }

    content_hash = hashlib.sha256(
        f"{item.user_id}{item.text}".encode()
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
                "user_id": item.user_id, 
                "type": "browsing_event", 
                "created_at": str(datetime.datetime.now())
            }
        )]
    )
    return {"status": "raw_data_saved", "id": point_id}

@app.get("/search")
def search_memory(query: str, user_id: str = "default_user"):
    return {"results": m.search(query, user_id=user_id)}

@app.post("/chat")
def chat_with_memory(item: UserInput):
    query_vector = get_embedding(item.text)
    if not query_vector: return {"reply": "Embedding Error", "context_used": []}

    try:
        search_response = client.query_points(collection_name=COLLECTION_NAME, query=query_vector, limit=5)
        search_hits = search_response.points
    except:
        return {"reply": "Database Error", "context_used": []}
    
    context_str = ""
    simple_sources = []
    
    for hit in search_hits:
        mem_text = hit.payload.get('memory') or "Unknown info"
        context_str += f"- {mem_text}\n"
        simple_sources.append({"memory": mem_text})

    if not context_str.strip(): context_str = "No relevant personal memories found."
   
    system_prompt = f"You are a helpful Personal OS. Use memories to answer:\n{context_str}"
    
    try:
        ollama_res = requests.post(f"{OLLAMA_URL}/api/chat", json={
            "model": "llama3.1:latest",
            "messages": [{"role": "system", "content": system_prompt}, {"role": "user", "content": item.text}],
            "stream": False
        })
        ai_reply = ollama_res.json().get("message", {}).get("content", "Error.")
        return {"reply": ai_reply, "context_used": simple_sources}
    except Exception as e:
        logger.error(f"Generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))