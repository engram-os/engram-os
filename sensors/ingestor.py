import os
import time
import shutil
import requests
import logging
import pypdf  


API_URL = "http://localhost:8000/ingest"
INBOX_DIR = "/Users/varunsalian/AI_Inbox" 
PROCESSED_DIR = os.path.join(INBOX_DIR, "processed")


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)


os.makedirs(INBOX_DIR, exist_ok=True)
os.makedirs(PROCESSED_DIR, exist_ok=True)

def extract_text(filepath):
    """Smart text extractor for PDF and Text files."""
    filename = os.path.basename(filepath)
    ext = os.path.splitext(filename)[1].lower()
    
    try:
        if ext == '.pdf':
            reader = pypdf.PdfReader(filepath)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
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
    try:
        files = [f for f in os.listdir(INBOX_DIR) if os.path.isfile(os.path.join(INBOX_DIR, f))]
    except FileNotFoundError:
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
            
            shutil.move(filepath, os.path.join(PROCESSED_DIR, filename))
            continue

        
        try:
            res = requests.post(API_URL, json={"text": content, "user_id": "file_watcher"})
            
            if res.status_code == 200:
                logger.info(f"Ingested Memory")
                
                destination = os.path.join(PROCESSED_DIR, filename)
                

                if os.path.exists(destination):
                    timestamp = int(time.time())
                    root, ext = os.path.splitext(filename)
                    destination = os.path.join(PROCESSED_DIR, f"{root}_{timestamp}{ext}")
                
                shutil.move(filepath, destination)
                logger.info(f"-> Moved to 'processed/'")
            else:
                logger.error(f"API Error: {res.status_code}")
                
        except Exception as e:
            logger.error(f"Connection Failed: {e}")

if __name__ == "__main__":
    logger.info(f"File Watcher Active. Monitoring '{INBOX_DIR}'...")
    logger.info(f"(Files will be moved to '{PROCESSED_DIR}' after reading)")
    
    while True:
        scan_inbox()
        time.sleep(5)