import sqlite3
import datetime
import hashlib
import hmac
import os
import threading

# ── Startup guard ──────────────────────────────────────────────────────────────
# Fail hard at import time if the secret is missing — a missing secret means
# every hash computed would be invalid, silently producing an unverifiable log.
_raw_secret = os.getenv("AUDIT_HMAC_SECRET", "")
if not _raw_secret:
    raise RuntimeError(
        "AUDIT_HMAC_SECRET env var is required but not set. "
        "Generate one with: python3 -c \"import secrets; print(secrets.token_hex(32))\""
    )
_AUDIT_SECRET: bytes = _raw_secret.encode()

current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
DBS_DIR = os.path.join(root_dir, "data", "dbs")
os.makedirs(DBS_DIR, exist_ok=True)
DB_PATH = os.path.join(DBS_DIR, "agent_activity.db")

# Sentinel hash used as prev_entry_hash for the very first row.
_GENESIS_HASH = "0" * 64

# Module-level lock — ensures the read-last-hash → compute-id → insert sequence
# is atomic even when multiple Celery workers call log_agent_action concurrently.
_write_lock = threading.Lock()


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def _compute_entry_hash(
    id_: int,
    timestamp: str,
    actor_id: str,
    action_type: str,
    resource_id: str,
    prev_hash: str,
) -> str:
    message = f"{id_}|{timestamp}|{actor_id}|{action_type}|{resource_id}|{prev_hash}"
    return hmac.new(_AUDIT_SECRET, message.encode(), hashlib.sha256).hexdigest()


def init_db() -> None:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")

    # Detect old schema (missing entry_hash column) and migrate cleanly.
    existing_cols = {
        row[1] for row in conn.execute("PRAGMA table_info(activity_log)").fetchall()
    }
    if "entry_hash" not in existing_cols:
        conn.execute("DROP TABLE IF EXISTS activity_log")

    conn.execute("""
        CREATE TABLE IF NOT EXISTS activity_log (
            id              INTEGER PRIMARY KEY,
            timestamp_wall  TEXT    NOT NULL,
            actor_id        TEXT    NOT NULL,
            action_type     TEXT    NOT NULL,
            resource_id     TEXT    NOT NULL DEFAULT '',
            matter_id       TEXT    NOT NULL DEFAULT '',
            details         TEXT    NOT NULL DEFAULT '',
            details_hash    TEXT    NOT NULL,
            prev_entry_hash TEXT    NOT NULL,
            entry_hash      TEXT    NOT NULL
        )
    """)
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_activity_log_id ON activity_log(id DESC)"
    )

    # Append-only enforcement — both triggers use RAISE(ABORT, ...) so the
    # offending statement is rolled back and an exception propagates to the caller.
    conn.execute("""
        CREATE TRIGGER IF NOT EXISTS prevent_update
        BEFORE UPDATE ON activity_log
        BEGIN
            SELECT RAISE(ABORT, 'audit log is append-only');
        END
    """)
    conn.execute("""
        CREATE TRIGGER IF NOT EXISTS prevent_delete
        BEFORE DELETE ON activity_log
        BEGIN
            SELECT RAISE(ABORT, 'audit log is append-only');
        END
    """)

    conn.commit()
    conn.close()


init_db()


def _get_last_entry_hash(conn: sqlite3.Connection) -> str:
    row = conn.execute(
        "SELECT entry_hash FROM activity_log ORDER BY id DESC LIMIT 1"
    ).fetchone()
    return row[0] if row else _GENESIS_HASH


def log_agent_action(
    agent_name: str,
    action_type: str,
    details: str,
    resource_id: str = "",
    matter_id: str = "",
) -> None:
    """
    Append a tamper-evident entry to the audit log.

    Signature is backward-compatible — all existing callers pass only
    (agent_name, action_type, details) and continue to work unchanged.
    """
    try:
        with _write_lock:
            conn = sqlite3.connect(DB_PATH, check_same_thread=False)
            conn.execute("PRAGMA journal_mode=WAL")

            timestamp = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
            prev_hash = _get_last_entry_hash(conn)

            # Pre-compute the next id so we can include it in the hash before
            # inserting — necessary because the prevent_update trigger blocks any
            # post-insert UPDATE that would otherwise set the final entry_hash.
            next_id: int = conn.execute(
                "SELECT COALESCE(MAX(id), 0) + 1 FROM activity_log"
            ).fetchone()[0]

            details_hash = _sha256(details)
            entry_hash = _compute_entry_hash(
                next_id, timestamp, agent_name, action_type, resource_id, prev_hash
            )

            conn.execute(
                """
                INSERT INTO activity_log
                    (id, timestamp_wall, actor_id, action_type, resource_id,
                     matter_id, details, details_hash, prev_entry_hash, entry_hash)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    next_id, timestamp, agent_name, action_type, resource_id,
                    matter_id, details, details_hash, prev_hash, entry_hash,
                ),
            )
            conn.commit()
            conn.close()
    except Exception as e:
        print(f"Logging failed: {e}")


def get_recent_logs(limit: int = 20) -> list:
    """Fetch recent logs for the dashboard. Returns same tuple shape as before."""
    try:
        if not os.path.exists(DB_PATH):
            return []
        conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        data = conn.execute(
            "SELECT timestamp_wall, actor_id, action_type, details "
            "FROM activity_log ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
        conn.close()
        return data
    except Exception:
        return []


def verify_audit_chain() -> dict:
    """
    Walk every row in insertion order and verify the HMAC chain is unbroken.

    Returns {"valid": True, "entries_checked": N} on success, or
    {"valid": False, "first_failed_id": N} on the first broken link.
    """
    try:
        conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        rows = conn.execute(
            "SELECT id, timestamp_wall, actor_id, action_type, resource_id, "
            "prev_entry_hash, entry_hash FROM activity_log ORDER BY id ASC"
        ).fetchall()
        conn.close()
    except Exception as e:
        return {"valid": False, "error": str(e)}

    if not rows:
        return {"valid": True, "entries_checked": 0}

    expected_prev = _GENESIS_HASH
    for row in rows:
        id_, timestamp, actor_id, action_type, resource_id, prev_hash, stored_hash = row

        if prev_hash != expected_prev:
            return {"valid": False, "first_failed_id": id_}

        computed = _compute_entry_hash(
            id_, timestamp, actor_id, action_type, resource_id, prev_hash
        )
        if computed != stored_hash:
            return {"valid": False, "first_failed_id": id_}

        expected_prev = stored_hash

    return {"valid": True, "entries_checked": len(rows)}
