"""
Tests for core/auth.py — get_current_user enforcement behavior.

Scope: the auth function itself, not endpoint wiring.
The Depends(get_current_user) on each router endpoint is code-review-verifiable;
the behavior of the auth logic is what needs a test.
"""
import pytest
from unittest.mock import patch
from fastapi import HTTPException
from core.user_registry import User


def test_dev_mode_when_no_api_key_set(monkeypatch):
    """ENGRAM_API_KEY unset → dev passthrough → synthetic admin returned."""
    monkeypatch.setenv("ENGRAM_API_KEY", "")
    from core.auth import get_current_user
    user = get_current_user(raw_key=None)
    assert user.role == "admin"
    assert user.display_name == "local-admin"


def test_auth_rejects_missing_key_when_enforced(monkeypatch):
    """ENGRAM_API_KEY set + no X-API-Key header → 403."""
    monkeypatch.setenv("ENGRAM_API_KEY", "test-secret")
    from core.auth import get_current_user
    with pytest.raises(HTTPException) as exc:
        get_current_user(raw_key=None)
    assert exc.value.status_code == 403


def test_auth_rejects_invalid_key(monkeypatch):
    """ENGRAM_API_KEY set + wrong key → 403."""
    monkeypatch.setenv("ENGRAM_API_KEY", "test-secret")
    with patch("core.auth.get_user_by_key", return_value=None):
        from core.auth import get_current_user
        with pytest.raises(HTTPException) as exc:
            get_current_user(raw_key="not-the-right-key")
    assert exc.value.status_code == 403


def test_auth_accepts_valid_key(monkeypatch):
    """ENGRAM_API_KEY set + correct key → User returned."""
    monkeypatch.setenv("ENGRAM_API_KEY", "test-secret")
    mock_user = User(id="u-test-001", role="user", display_name="Tester")
    with patch("core.auth.get_user_by_key", return_value=mock_user):
        from core.auth import get_current_user
        user = get_current_user(raw_key="correct-key")
    assert user.id == "u-test-001"
    assert user.role == "user"
