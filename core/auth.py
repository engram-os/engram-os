"""core/auth.py — FastAPI auth dependencies shared across all routers.

Extracted from brain.py so mounted routers can import Depends(get_current_user)
without creating circular imports back into brain.py.
"""
import os
from fastapi import Depends, HTTPException, Security
from fastapi.security import APIKeyHeader
from core.identity import get_or_create_identity
from core.user_registry import get_user_by_key, User

_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

_IDENTITY = get_or_create_identity()
LOCAL_USER_ID = _IDENTITY["user_id"]


def get_current_user(raw_key: str | None = Security(_api_key_header)) -> User:
    """Resolve the caller to a User.

    Dev mode (ENGRAM_API_KEY unset): all requests receive a synthetic admin
    backed by the local machine identity — zero behaviour change for
    single-user deployments.

    Enforced mode (ENGRAM_API_KEY set): X-API-Key header required and
    validated against the user registry. Missing or invalid key → 403.

    os.getenv is called inside the function body, not at module level, so
    tests can monkeypatch ENGRAM_API_KEY without requiring a module reload.
    """
    api_key = os.getenv("ENGRAM_API_KEY")
    if not api_key:
        return User(id=LOCAL_USER_ID, role="admin", display_name="local-admin")
    if not raw_key:
        raise HTTPException(status_code=403, detail="X-API-Key header required.")
    user = get_user_by_key(raw_key)
    if not user:
        raise HTTPException(status_code=403, detail="Invalid API key.")
    return user


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """Assert the current user is an admin."""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required.")
    return current_user
