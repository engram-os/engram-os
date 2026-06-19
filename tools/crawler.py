import logging
import os
import time
from core.network_gateway import gateway
from bs4 import BeautifulSoup
from collections import deque
from urllib.parse import urljoin, urlparse
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct
import uuid

_MAX_RETRIES = 3
_RETRY_BACKOFF = 2  # base seconds; actual delay = _RETRY_BACKOFF ** attempt

logger = logging.getLogger(__name__)
LLM_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1:latest")

OLLAMA_URL = os.getenv("OLLAMA_HOST", "http://host.docker.internal:11434")
QDRANT_HOST = os.getenv("QDRANT_HOST", "qdrant")
DOC_COLLECTION = "doc_knowledge"

qdrant_docs = QdrantClient(host=QDRANT_HOST, port=6333)


def _ensure_doc_collection():
    if not qdrant_docs.collection_exists(DOC_COLLECTION):
        qdrant_docs.create_collection(
            collection_name=DOC_COLLECTION,
            vectors_config=VectorParams(size=768, distance=Distance.COSINE),
        )


_ensure_doc_collection()

class DocSpider:
    def __init__(self, base_url, max_pages=20):
        self.base_url = base_url
        self.domain = urlparse(base_url).netloc
        self.max_pages = max_pages
        self.visited: set[str] = set()
        # Tracks every URL ever enqueued so we never add the same URL twice.
        # Without this the queue grows O(links × pages) for sites with heavy
        # cross-linking, wasting memory and retrying already-queued URLs.
        self.queued: set[str] = {base_url}

    def is_valid_url(self, url):
        """Return True if url is on the same domain and not already queued."""
        parsed = urlparse(url)
        return parsed.netloc == self.domain and url not in self.queued

    def _fetch_with_retry(self, url: str):
        """GET url, retrying up to _MAX_RETRIES times on 5xx responses.

        4xx errors are permanent (bad URL) — returned immediately without retry.
        Connection exceptions are retried with exponential backoff.
        """
        last_exc: Exception | None = None
        response = None
        for attempt in range(_MAX_RETRIES):
            try:
                response = gateway.get("crawler", url, timeout=5)
                if response.status_code < 500:
                    return response
                if attempt < _MAX_RETRIES - 1:
                    wait = _RETRY_BACKOFF ** attempt
                    logger.warning(
                        f"HTTP {response.status_code} for {url} — "
                        f"retry {attempt + 1}/{_MAX_RETRIES} in {wait}s"
                    )
                    time.sleep(wait)
            except Exception as exc:
                last_exc = exc
                if attempt < _MAX_RETRIES - 1:
                    wait = _RETRY_BACKOFF ** attempt
                    logger.warning(f"Request error for {url}: {exc} — retry {attempt + 1}/{_MAX_RETRIES} in {wait}s")
                    time.sleep(wait)
        if last_exc:
            raise last_exc
        return response  # final 5xx response after all retries exhausted

    def clean_text(self, text):
        """Remove excess whitespace"""
        return " ".join(text.split())

    def crawl(self):
        queue = deque([self.base_url])
        pages_crawled = 0
        
        logger.info(f"Doc-Spider starting on: {self.base_url}")
        
        while queue and pages_crawled < self.max_pages:
            current_url = queue.popleft()
            if current_url in self.visited:
                continue

            try:
                logger.debug(f"Reading: {current_url}")
                response = self._fetch_with_retry(current_url)
                if response.status_code != 200:
                    continue

                soup = BeautifulSoup(response.content, 'html.parser')
                self.visited.add(current_url)
                pages_crawled += 1

                # --- INTELLIGENT PARSING ---

                # 1. Extract Code Blocks (High Value)
                code_blocks = soup.find_all('pre')
                for code in code_blocks:
                    code_text = code.get_text()
                    if len(code_text) > 20:
                        self.save_knowledge(code_text, current_url, type="code")

                # 2. Extract Prose (Paragraphs)
                paragraphs = soup.find_all('p')
                buffer = ""
                for p in paragraphs:
                    text = self.clean_text(p.get_text())
                    if len(text) > 50:
                        buffer += text + " "
                        if len(buffer) > 500:
                            self.save_knowledge(buffer, current_url, type="text")
                            buffer = ""

                # 3. Find new links — is_valid_url checks queued, not visited,
                #    so each URL is enqueued at most once.
                for link in soup.find_all('a', href=True):
                    full_url = urljoin(current_url, link['href'])
                    if self.is_valid_url(full_url):
                        queue.append(full_url)
                        self.queued.add(full_url)

            except Exception as e:
                logger.warning(f"Failed to crawl {current_url}: {e}")

        logger.info(f"Crawl complete. Ingested {pages_crawled} pages.")

    def save_knowledge(self, content, source_url, type="text"):
        """Vectorize and store in Qdrant doc_knowledge collection"""
        try:
            res = gateway.post("ollama", "/api/embeddings", json={
                "model": "nomic-embed-text:latest",
                "prompt": content
            }, timeout=30)
            vector = res.json()["embedding"]
        except Exception as e:
            logger.error(f"Embedding failed for {source_url}: {e}")
            return

        qdrant_docs.upsert(
            collection_name=DOC_COLLECTION,
            points=[PointStruct(
                id=str(uuid.uuid4()),
                vector=vector,
                payload={"content": content, "source": source_url, "type": type},
            )]
        )

# -- Standalone Test --
if __name__ == "__main__":
    spider = DocSpider("https://flask.palletsprojects.com/en/3.0.x/quickstart/", max_pages=5)
    spider.crawl()