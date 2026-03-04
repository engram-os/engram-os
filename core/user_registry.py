"""
core/user_registry.py — Per-user identity and API key registry.

SQLite-backed. DB_PATH is a module-level variable so tests can monkeypatch it
to an isolated per-test path without touching the real database.

Key storage: SHA256(raw_key) — the raw key is NEVER persisted. It is returned
once on user creation and must be stored by the caller.
"""
import os
import uuid
import hashlib
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

# Module-level path: readable by _get_conn() dynamically so monkeypatching
# (ur.DB_PATH = tmp_path) works correctly in tests.
DB_PATH: str = os.getenv("USERS_DB_PATH", "data/dbs/users.db")


@dataclass
class User:
    id: str
    role: str           # "admin" | "user"
    display_name: str


# ─── Internal helpers ─────────────────────────────────────────────────────────

def _get_conn() -> sqlite3.Connection:
    dir_name = os.path.dirname(DB_PATH)
    if dir_name:
        os.makedirs(dir_name, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def _hash_key(raw_key: str) -> str:
    return hashlib.sha256(raw_key.encode()).hexdigest()


# ─── Public API ───────────────────────────────────────────────────────────────

def init_user_db() -> None:
    """Create the users table and index if they don't exist."""
    with _get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id            TEXT PRIMARY KEY,
                api_key_hash  TEXT UNIQUE NOT NULL,
                role          TEXT NOT NULL DEFAULT 'user',
                display_name  TEXT NOT NULL DEFAULT '',
                created_at    TEXT NOT NULL
            )
        """)
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_users_api_key ON users(api_key_hash)"
        )


def bootstrap_admin(user_id: str, raw_api_key: str) -> None:
    """Seed the admin row if the registry is empty.

    Called once at brain startup. Idempotent — does nothing if any user
    already exists. In dev mode (raw_api_key=''), stores an empty hash so
    the row exists but no real key can match it.
    """
    init_user_db()
    with _get_conn() as conn:
        count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        if count == 0:
            key_hash = _hash_key(raw_api_key) if raw_api_key else ""
            conn.execute(
                "INSERT INTO users (id, api_key_hash, role, display_name, created_at) "
                "VALUES (?, ?, 'admin', 'Admin', ?)",
                (user_id, key_hash, str(datetime.now()))
            )


def get_user_by_key(raw_key: str) -> Optional[User]:
    """Look up a user by their raw API key. Returns None if not found."""
    key_hash = _hash_key(raw_key)
    with _get_conn() as conn:
        row = conn.execute(
            "SELECT id, role, display_name FROM users WHERE api_key_hash = ?",
            (key_hash,)
        ).fetchone()
    if row is None:
        return None
    return User(id=row["id"], role=row["role"], display_name=row["display_name"])


def create_user(display_name: str, role: str = "user") -> tuple[str, str]:
    """Create a new user. Returns (user_id, raw_api_key).

    The raw key is shown once and never stored — caller must record it.
    """
    init_user_db()
    user_id = str(uuid.uuid4())
    raw_key = uuid.uuid4().hex + uuid.uuid4().hex  # 64-char random key
    with _get_conn() as conn:
        conn.execute(
            "INSERT INTO users (id, api_key_hash, role, display_name, created_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (user_id, _hash_key(raw_key), role, display_name, str(datetime.now()))
        )
    return user_id, raw_key


def list_users() -> list[dict]:
    """Return all users. Never includes api_key_hash."""
    with _get_conn() as conn:
        rows = conn.execute(
            "SELECT id, role, display_name, created_at FROM users"
        ).fetchall()
    return [dict(row) for row in rows]


def get_user_by_id(user_id: str) -> Optional[User]:
    """Look up a user by their ID. Returns None if not found."""
    with _get_conn() as conn:
        row = conn.execute(
            "SELECT id, role, display_name FROM users WHERE id = ?",
            (user_id,)
        ).fetchone()
    if row is None:
        return None
    return User(id=row["id"], role=row["role"], display_name=row["display_name"])
