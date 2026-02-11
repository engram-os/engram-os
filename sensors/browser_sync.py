import os
import sqlite3
import shutil
import time
import requests
import logging
from datetime import datetime

current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)

DATA_DIR = os.path.join(root_dir, "data")
DBS_DIR = os.path.join(DATA_DIR, "dbs")

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(DBS_DIR, exist_ok=True)

TIMESTAMP_FILE = os.path.join(DATA_DIR, ".last_browser_sync")
TEMP_DB = os.path.join(DBS_DIR, "history_copy.db")

HISTORY_PATH = os.path.expanduser("~/Library/Application Support/Google/Chrome/Default/History")

API_URL = "http://localhost:8000/ingest"

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

def get_last_timestamp():
    """Reads the last sync time from the data folder."""
    if os.path.exists(TIMESTAMP_FILE):
        try:
            with open(TIMESTAMP_FILE, "r") as f:
                return float(f.read().strip())
        except:
            return 0.0
    return 0.0

def save_last_timestamp(ts):
    """Saves the sync time to the data folder."""
    with open(TIMESTAMP_FILE, "w") as f:
        f.write(str(ts))

def sync_history():
    last_sync = get_last_timestamp()

    if not os.path.exists(HISTORY_PATH):
        logger.error(f"Browser history not found at: {HISTORY_PATH}")
        return

    try:
        shutil.copy2(HISTORY_PATH, TEMP_DB)
    except Exception as e:
        logger.error(f"Could not copy DB: {e}")
        return

    try:
        conn = sqlite3.connect(TEMP_DB)
        cursor = conn.cursor()

        webkit_last_sync = (last_sync + 11644473600) * 1000000

        query = """
            SELECT url, title, last_visit_time 
            FROM urls 
            WHERE last_visit_time > ? 
            AND title != ''
            ORDER BY last_visit_time DESC
        """
        
        cursor.execute(query, (webkit_last_sync,))
        rows = cursor.fetchall()
        
        new_max_time = last_sync
        
        if rows:
            logger.info(f"Found {len(rows)} new pages visited.")
        
        for url, title, visit_time in rows:
            visit_time_sec = (visit_time / 1000000) - 11644473600
            readable_time = datetime.fromtimestamp(visit_time_sec).strftime('%Y-%m-%d %H:%M:%S')
            
            if visit_time_sec > new_max_time:
                new_max_time = visit_time_sec

            embed_text = f"User visited '{title}' ({url})"

            store_text = f"User visited '{title}' ({url}) on {readable_time}"
            
            try:
                requests.post(API_URL, json={
                    "text": store_text, 
                    "embed-text": embed_text,
                    "user_id": "browser_watcher",
                    "type": "browsing_event"
                    })
            except:
                logger.error("Failed to send to API")

        conn.close()
        
        if new_max_time > last_sync:
            save_last_timestamp(new_max_time)
            
    except Exception as e:
        logger.error(f"Error reading history DB: {e}")

if __name__ == "__main__":
    logger.info("---------------------------------------")
    logger.info(f"Browser Watcher Active.")
    logger.info(f"Storing temp DB in: {DBS_DIR}")
    logger.info(f"Storing timestamp in: {TIMESTAMP_FILE}")
    logger.info("---------------------------------------")
    
    while True:
        sync_history()
        time.sleep(60)