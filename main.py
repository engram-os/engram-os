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
from agents.tasks import run_calendar_agent
from agents.tasks import test_agent_pulse, run_calendar_agent, run_email_agent 
from agents.terminal import router as terminal_router
from agents.spectre import router as spectre_router
from systems.visualizer import router as visualizer_router
from fastapi.middleware.cors import CORSMiddleware
from agents.git_automator import router as git_router
from systems.crawler import DocSpider, collection 
from systems.pm_tools import IntegrationManager
from agents.git_automator import client
from agents.tasks import test_agent_pulse 


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI(title="My Local AI OS")

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


def get_embedding(text):
    """Asks Ollama to turn text into vectors directly."""
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
        return {"briefing": "You have no active tasks assigned in Jira or Linear. Enjoy your day!", "tasks": []}

    task_list_str = "\n".join([f"- [{t.source}] {t.priority}: {t.title} ({t.status})" for t in tasks])
    
    prompt = f"""
    You are an executive assistant. Here are the user's active tasks for today:
    
    {task_list_str}
    
    Write a concise "Daily Briefing" paragraph (max 3 sentences). 
    1. Highlight the most critical item first.
    2. Mention the total count.
    3. Keep it professional but encouraging.
    """
    
    response = client.chat(model='llama3', messages=[{'role': 'user', 'content': prompt}])
    
    return {
        "briefing": response['message']['content'],
        "tasks": tasks
    }    

# 1. Trigger Crawl
@app.post("/api/docs/ingest")
async def ingest_docs(request: CrawlRequest):
    spider = DocSpider(request.url, max_pages=request.max_pages)
    spider.crawl() 
    return {"status": "success", "message": f"Ingested {request.url}"}

# 2. RAG Query (The 'Chat with Docs' Feature)
class QueryRequest(BaseModel):
    query: str

@app.post("/api/docs/query")
async def query_docs(request: QueryRequest):
    # Retrieve top 3 most relevant chunks
    results = collection.query(
        query_texts=[request.query],
        n_results=3
    )
    
    # Format context for Llama 3
    context = ""
    sources = []
    
    if results['documents']:
        for i, doc in enumerate(results['documents'][0]):
            meta = results['metadatas'][0][i]
            context += f"\n--- Source: {meta['source']} ({meta['type']}) ---\n{doc}\n"
            sources.append(meta['source'])

    # Ask Llama 3 with the context
    prompt = f"""
    Answer the user question using strictly the context below. 
    If the code examples are in the context, prefer using them.
    
    CONTEXT:
    {context}
    
    QUESTION: {request.query}
    """
    
    from agents.git_automator import client 
    response = client.chat(model='llama3.1:latest', messages=[{'role': 'user', 'content': prompt}])
    
    return {
        "answer": response['message']['content'],
        "sources": list(set(sources))
    }    

@app.post("/trigger-agent")
async def trigger_agent_test():
    """Wakes up the background worker to check if it's alive."""
    
    task = test_agent_pulse.delay("Hello from API") 
    return {"message": "Agent triggered", "task_id": task.id}

@app.post("/run-agents/calendar")
async def trigger_calendar_check():
    """Manually forces the Calendar Agent to wake up and check recent memories."""
    task = run_calendar_agent.delay()
    return {"message": "Calendar Agent activated", "task_id": task.id}

@app.post("/add-memory")
def add_memory(item: UserInput):
    """Use this for PROFILE FACTS (Job, Likes, Name)."""
    logger.info(f"Mem0 Processing: {item.text}")
    m.add(item.text, user_id=item.user_id)
    return {"status": "profile_updated"}

@app.post("/ingest")
def ingest_file(item: UserInput):
    """Use this for RAW DATA (Files, Notes, Todos). Skips the LLM Judge."""
    logger.info(f"Direct Ingestion: {item.text[:50]}...")
    
    
    vector = get_embedding(item.text)
    if not vector:
        raise HTTPException(status_code=500, detail="Embedding failed")

    
    point_id = str(uuid.uuid4())
    client.upsert(
        collection_name=COLLECTION_NAME,
        points=[
            models.PointStruct(
                id=point_id,
                vector=vector,
                payload={
                    "memory": item.text, 
                    "user_id": item.user_id,
                    "type": "raw_ingestion",
                    "created_at": str(datetime.datetime.now())
                }
            )
        ]
    )
    return {"status": "raw_data_saved", "id": point_id}

@app.get("/search")
def search_memory(query: str, user_id: str = "default_user"):
    """Search EVERYTHING (Both Profile and Raw Data)."""
    return {"results": m.search(query, user_id=user_id)}

@app.post("/chat")
def chat_with_memory(item: UserInput):
    """RAG Endpoint: Uses Direct DB Search via Query API."""
    logger.info(f"Chat request: {item.text}")

    
    query_vector = get_embedding(item.text)
    
    if not query_vector:
        return {"reply": "Embedding Error", "context_used": []}

    try:
        search_response = client.query_points(
            collection_name=COLLECTION_NAME,
            query=query_vector,
            limit=5
        )
        search_hits = search_response.points
        
    except Exception as e:
        logger.error(f"Search failed: {e}")
        try:
            search_hits = client.search(
                collection_name=COLLECTION_NAME,
                query_vector=query_vector,
                limit=5
            )
        except:
             return {"reply": "Database Error", "context_used": []}

    
    context_str = ""
    simple_sources = []
    
    for hit in search_hits:
        payload = hit.payload
        mem_text = payload.get('memory') or payload.get('text') or payload.get('data') or "Unknown info"
        
        context_str += f"- {mem_text}\n"
        simple_sources.append({"memory": mem_text})

    if not context_str.strip():
        context_str = "No relevant personal memories found."

   
    system_prompt = f"""You are a helpful Personal OS. 
    Use the following memories to answer the user's question.
    
    USER MEMORIES:
    {context_str}
    
    If the answer isn't in the memories, say you don't know."""

    
    payload = {
        "model": "llama3.1:latest",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": item.text}
        ],
        "stream": False
    }

    try:
        ollama_res = requests.post(f"{OLLAMA_URL}/api/chat", json=payload)
        ai_reply = ollama_res.json().get("message", {}).get("content", "Error.")
        
        return {"reply": ai_reply, "context_used": simple_sources}
        
    except Exception as e:
        logger.error(f"Generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/run-agents/email")
async def trigger_email_check():
    """Manually forces the Email Agent to wake up."""
    task = run_email_agent.delay()
    return {"message": "Email Agent activated", "task_id": task.id}