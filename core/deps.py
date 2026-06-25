"""
Shared application state for all API routers.

Initialised once at import time. Routers import from here; brain.py
assembles them. No router should import from core.brain — that direction
creates circular imports.
"""
import os

from qdrant_client import QdrantClient

from core.llm_client import LLMEngine, OllamaEngine
from core.memory_client import EncryptedMemoryClient, load_encryption_key
from core.network_gateway import gateway

QDRANT_HOST = os.getenv("QDRANT_HOST", "qdrant")
COLLECTION_NAME = "second_brain"
LLM_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1:latest")

client = EncryptedMemoryClient(
    QdrantClient(host=QDRANT_HOST, port=6333),
    load_encryption_key(),
)

llm: LLMEngine = OllamaEngine(gateway, LLM_MODEL)


def get_embedding(text: str) -> list[float] | None:
    return llm.embed(text)
