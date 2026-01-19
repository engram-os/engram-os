import os
import sqlite3
import shutil
import time
import requests
import logging
from datetime import datetime


API_URL = "http://localhost:8000/ingest"
HISTORY_PATH = os.path.expanduser("~/Library/Application Support/Google/Chrome/Default/History")
TEMP_DB = "history_copy.db"

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

def get_last_timestamp():
    """Reads the last sync time from a local file."""
    if os.path.exists(".last_browser_sync"):
        with open(".last_browser_sync", "r") as f:
            return float(f.read().strip())
    return 0.0

def save_last_timestamp(ts):
    with open(".last_browser_sync", "w") as f:
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


        text = f"User visited the website '{title}' at URL: {url} on {readable_time}"
        
        try:
            requests.post(API_URL, json={"text": text, "user_id": "browser_watcher"})

        except:
            logger.error("   -> Failed to send to API")

    conn.close()
    

    if new_max_time > last_sync:
        save_last_timestamp(new_max_time)


if __name__ == "__main__":
    logger.info("Browser Watcher Started (Checking every 60 seconds)...")
    while True:
        sync_history()
        time.sleep(60) 