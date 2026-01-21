import sqlite3
import datetime
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)

DBS_DIR = os.path.join(root_dir, "data", "dbs")
os.makedirs(DBS_DIR, exist_ok=True)

DB_PATH = os.path.join(BASE_DIR, "agent_activity.db")

def init_db():
    """Creates the log table if it doesn't exist."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS activity_log
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  timestamp TEXT,
                  agent_name TEXT,
                  action_type TEXT,
                  details TEXT)''')
    conn.commit()
    conn.close()

def log_agent_action(agent_name, action_type, details):
    """
    action_type options: 'THINKING', 'TOOL_USE', 'DECISION', 'ERROR'
    """
    try:
        init_db() 
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        c.execute("INSERT INTO activity_log (timestamp, agent_name, action_type, details) VALUES (?, ?, ?, ?)",
                  (timestamp, agent_name, action_type, str(details)))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Logging failed: {e}")

def get_recent_logs(limit=20):
    """Fetches logs for the UI."""
    try:
        if not os.path.exists(DB_PATH):
            return []
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT timestamp, agent_name, action_type, details FROM activity_log ORDER BY id DESC LIMIT ?", (limit,))
        data = c.fetchall()
        conn.close()
        return data
    except:
        return []