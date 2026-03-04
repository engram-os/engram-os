"""
core/matter_registry.py — Matter/case/project isolation registry.

SQLite-backed. DB_PATH is a module-level variable so tests can monkeypatch it
to an isolated per-test path without touching the real database.

A "matter" is a named data partition — a legal case, a client project, a
medical record context, etc. Every Qdrant write is tagged with a matter_id.
Every read optionally filters by matter_id. Matters can be closed (hard-delete
of all Qdrant points happens in brain.py; registry just tracks status).

Access model:
  - Creator of a matter is automatically granted access.
  - Admin users bypass access checks (enforced in brain.py, not here).
  - grant_access is idempotent — safe to call multiple times.
"""
import os
import uuid
import sqlite3
from datetime import datetime
from typing import Optional

DB_PATH: str = os.getenv("MATTER_DB_PATH", "data/dbs/matter_registry.db")


# ─── Internal helpers ─────────────────────────────────────────────────────────

def _get_conn() -> sqlite3.Connection:
    dir_name = os.path.dirname(DB_PATH)
    if dir_name:
        os.makedirs(dir_name, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


# ─── Public API ───────────────────────────────────────────────────────────────

def init_matter_db() -> None:
    """Create tables and indexes if they don't exist."""
    with _get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS matters (
                id          TEXT PRIMARY KEY,
                name        TEXT NOT NULL,
                status      TEXT NOT NULL DEFAULT 'open',
                created_by  TEXT NOT NULL,
                created_at  TEXT NOT NULL,
                closed_at   TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS user_matter_access (
                user_id     TEXT NOT NULL,
                matter_id   TEXT NOT NULL,
                granted_by  TEXT NOT NULL,
                granted_at  TEXT NOT NULL,
                PRIMARY KEY (user_id, matter_id)
            )
        """)
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_uma_user ON user_matter_access(user_id)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_uma_matter ON user_matter_access(matter_id)"
        )


def bootstrap_default_matter(admin_user_id: str) -> None:
    """Ensure the 'default' personal matter exists and admin has access.

    Called at brain startup. Idempotent.
    """
    init_matter_db()
    with _get_conn() as conn:
        exists = conn.execute(
            "SELECT id FROM matters WHERE id = 'default'"
        ).fetchone()
        if not exists:
            conn.execute(
                "INSERT INTO matters (id, name, status, created_by, created_at) "
                "VALUES ('default', 'Personal', 'open', ?, ?)",
                (admin_user_id, str(datetime.now()))
            )
            conn.execute(
                "INSERT OR IGNORE INTO user_matter_access "
                "(user_id, matter_id, granted_by, granted_at) VALUES (?, 'default', ?, ?)",
                (admin_user_id, admin_user_id, str(datetime.now()))
            )


def create_matter(name: str, created_by: str) -> str:
    """Create a new matter. Creator is automatically granted access.
    Returns the new matter_id.
    """
    init_matter_db()
    matter_id = str(uuid.uuid4())
    now = str(datetime.now())
    with _get_conn() as conn:
        conn.execute(
            "INSERT INTO matters (id, name, status, created_by, created_at) "
            "VALUES (?, ?, 'open', ?, ?)",
            (matter_id, name, created_by, now)
        )
        conn.execute(
            "INSERT INTO user_matter_access "
            "(user_id, matter_id, granted_by, granted_at) VALUES (?, ?, ?, ?)",
            (created_by, matter_id, created_by, now)
        )
    return matter_id


def get_matter(matter_id: str) -> Optional[dict]:
    """Return a matter dict or None if not found."""
    with _get_conn() as conn:
        row = conn.execute(
            "SELECT id, name, status, created_by, created_at, closed_at "
            "FROM matters WHERE id = ?",
            (matter_id,)
        ).fetchone()
    return dict(row) if row else None


def list_matters_for_user(user_id: str) -> list[dict]:
    """Return open matters the user has access to."""
    with _get_conn() as conn:
        rows = conn.execute(
            """
            SELECT m.id, m.name, m.status, m.created_by, m.created_at
            FROM matters m
            JOIN user_matter_access a ON m.id = a.matter_id
            WHERE a.user_id = ? AND m.status = 'open'
            """,
            (user_id,)
        ).fetchall()
    return [dict(row) for row in rows]


def check_access(user_id: str, matter_id: str) -> bool:
    """Return True if user_id has an access row for matter_id."""
    with _get_conn() as conn:
        row = conn.execute(
            "SELECT 1 FROM user_matter_access WHERE user_id = ? AND matter_id = ?",
            (user_id, matter_id)
        ).fetchone()
    return row is not None


def grant_access(matter_id: str, user_id: str, granted_by: str) -> None:
    """Grant a user access to a matter. Idempotent (INSERT OR IGNORE)."""
    with _get_conn() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO user_matter_access "
            "(user_id, matter_id, granted_by, granted_at) VALUES (?, ?, ?, ?)",
            (user_id, matter_id, granted_by, str(datetime.now()))
        )


def close_matter(matter_id: str, closed_by: str) -> None:
    """Mark a matter as closed. Qdrant point deletion is handled by brain.py."""
    with _get_conn() as conn:
        conn.execute(
            "UPDATE matters SET status = 'closed', closed_at = ? WHERE id = ?",
            (str(datetime.now()), matter_id)
        )
