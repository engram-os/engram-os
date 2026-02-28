import os
import signal
import sys
import time
import shutil
import requests
import logging
import pypdf
import docx
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
            
        elif ext == '.docx':
            doc = docx.Document(filepath)
            text = "\n".join(p.text for p in doc.paragraphs if p.text.strip())
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

    had_error = False
    for filename in files:
        if filename.startswith("."): continue 
        
        filepath = os.path.join(INBOX_DIR, filename)
        logger.info(f"Detected: {filename}")
        
        content = extract_text(filepath)
        
        if not content:
            logger.warning(f"   Skipping unknown file type: {filename}")
            try:
                shutil.move(filepath, os.path.join(PROCESSED_DIR, filename))
            except Exception:
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
                had_error = True

        except Exception as e:
            logger.error(f"Connection Failed (Is the Brain online?): {e}")
            had_error = True

    return had_error

def _handle_shutdown(sig, frame):
    logger.info(f"Received signal {sig}. File watcher shutting down cleanly.")
    sys.exit(0)

if __name__ == "__main__":
    signal.signal(signal.SIGTERM, _handle_shutdown)
    signal.signal(signal.SIGINT, _handle_shutdown)

    print("------------------------------------------------")
    logger.info(f"File Watcher Active.")
    logger.info(f"Watching: {INBOX_DIR}")
    logger.info(f"Drop files there to ingest them.")
    print("------------------------------------------------")
    
    BASE_SLEEP = 5
    MAX_SLEEP = 300
    consecutive_errors = 0

    while True:
        had_error = scan_inbox()
        if had_error:
            consecutive_errors += 1
            sleep_for = min(BASE_SLEEP * (2 ** consecutive_errors), MAX_SLEEP)
            logger.warning(f"API errors detected. Backing off for {sleep_for}s (attempt {consecutive_errors})")
        else:
            consecutive_errors = 0
            sleep_for = BASE_SLEEP
        time.sleep(sleep_for)