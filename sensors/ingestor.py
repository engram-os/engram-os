import os
import time
import shutil
import requests
import logging
import pypdf
from identity import get_or_create_identity

API_URL = os.getenv("INGEST_API_URL", "http://localhost:8000/ingest")

current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)

INBOX_DIR = os.path.join(root_dir, "data", "inbox") 
PROCESSED_DIR = os.path.join(INBOX_DIR, "processed")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

IDENTITY = get_or_create_identity()
LOCAL_USER_ID = IDENTITY["user_id"]

os.makedirs(INBOX_DIR, exist_ok=True)
os.makedirs(PROCESSED_DIR, exist_ok=True)

def extract_text(filepath):
    """Smart text extractor for PDF and Text files."""
    filename = os.path.basename(filepath)
    ext = os.path.splitext(filename)[1].lower()
    
    try:
        if ext == '.pdf':
            reader = pypdf.PdfReader(filepath)
            parts = []
            for page in reader.pages:
                parts.append(page.extract_text() or "")
            text = "\n".join(parts)
            return f"File '{filename}': {text}"
            
        elif ext in ['.txt', '.md', '.py', '.js', '.csv', '.json']:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                return f"File '{filename}': {f.read()}"
                
        else:
            return None
    except Exception as e:
        logger.error(f"Failed to read {filename}: {e}")
        return None

def scan_inbox():
    if not os.path.exists(INBOX_DIR):
        logger.error(f"Inbox directory not found: {INBOX_DIR}")
        return

    try:
        files = [f for f in os.listdir(INBOX_DIR) if os.path.isfile(os.path.join(INBOX_DIR, f))]
    except Exception as e:
        logger.error(f"Error reading inbox: {e}")
        return

    if not files:
        return

    for filename in files:
        if filename.startswith("."): continue 
        
        filepath = os.path.join(INBOX_DIR, filename)
        logger.info(f"Detected: {filename}")
        
        content = extract_text(filepath)
        
        if not content:
            logger.warning(f"   Skipping unknown file type: {filename}")
            try:
                shutil.move(filepath, os.path.join(PROCESSED_DIR, filename))
            except:
                pass
            continue

        try:
            res = requests.post(API_URL, json={"text": content, "user_id": LOCAL_USER_ID}, timeout=(5, 10))
            
            if res.status_code == 200:
                logger.info(f"Ingested Memory")

                destination = os.path.join(PROCESSED_DIR, filename)
                if os.path.exists(destination):
                    timestamp = int(time.time() * 1000)
                    root, ext = os.path.splitext(filename)
                    destination = os.path.join(PROCESSED_DIR, f"{root}_{timestamp}{ext}")
                
                shutil.move(filepath, destination)
                logger.info(f"-> Moved to 'processed/'")
            else:
                logger.error(f"API Error: {res.status_code}")
                
        except Exception as e:
            logger.error(f"Connection Failed (Is the Brain online?): {e}")

if __name__ == "__main__":
    print("------------------------------------------------")
    logger.info(f"File Watcher Active.")
    logger.info(f"Watching: {INBOX_DIR}")
    logger.info(f"Drop files there to ingest them.")
    print("------------------------------------------------")
    
    while True:
        scan_inbox()
        time.sleep(5)