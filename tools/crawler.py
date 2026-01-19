import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import chromadb
from chromadb.utils import embedding_functions
import uuid

chroma_client = chromadb.PersistentClient(path="./engram_db")

ef = embedding_functions.DefaultEmbeddingFunction()

collection = chroma_client.get_or_create_collection(name="doc_knowledge", embedding_function=ef)

class DocSpider:
    def __init__(self, base_url, max_pages=20):
        self.base_url = base_url
        self.domain = urlparse(base_url).netloc
        self.max_pages = max_pages
        self.visited = set()
        
    def is_valid_url(self, url):
        """Ensure we stay on the same documentation site"""
        parsed = urlparse(url)
        return parsed.netloc == self.domain and url not in self.visited

    def clean_text(self, text):
        """Remove excess whitespace"""
        return " ".join(text.split())

    def crawl(self):
        queue = [self.base_url]
        pages_crawled = 0
        
        print(f"Doc-Spider starting on: {self.base_url}")
        
        while queue and pages_crawled < self.max_pages:
            current_url = queue.pop(0)
            if current_url in self.visited:
                continue
            
            try:
                print(f"   Reading: {current_url}")
                response = requests.get(current_url, timeout=5)
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
                
                # 3. Find new links
                for link in soup.find_all('a', href=True):
                    full_url = urljoin(current_url, link['href'])
                    if self.is_valid_url(full_url):
                        queue.append(full_url)
                        
            except Exception as e:
                print(f" Failed to crawl {current_url}: {e}")

        print(f" Crawl Complete. Ingested {pages_crawled} pages.")

    def save_knowledge(self, content, source_url, type="text"):
        """Vectorize and store in ChromaDB"""
        collection.add(
            documents=[content],
            metadatas=[{"source": source_url, "type": type}],
            ids=[str(uuid.uuid4())]
        )

# -- Standalone Test --
if __name__ == "__main__":
    spider = DocSpider("https://flask.palletsprojects.com/en/3.0.x/quickstart/", max_pages=5)
    spider.crawl()