"""
Test suite bootstrap — stubs heavy third-party and project modules before any
project code is imported.  This file is loaded by pytest before test collection
begins, so all sys.modules entries below are in place before the first import.
"""
import os
import sys
from unittest.mock import MagicMock
from fastapi import APIRouter

# ── Third-party packages that connect to external services at import time ─────
for _mod in [
    "mem0",
    "qdrant_client", "qdrant_client.http", "qdrant_client.http.models",
    "chromadb",
    "ollama",
    "celery", "celery.app", "celery.schedules",
    "redis",
    "google.auth", "google.auth.transport", "google.auth.transport.requests",
    "google.oauth2", "google.oauth2.credentials",
    "google_auth_oauthlib", "google_auth_oauthlib.flow",
    "googleapiclient", "googleapiclient.discovery",
    "streamlit",
    "jira",
    "watchdog", "watchdog.observers", "watchdog.events",
    "bs4",
    "pypdf",
    "dateutil", "dateutil.parser",
]:
    sys.modules.setdefault(_mod, MagicMock())

# ── Project modules with heavy runtime side-effects ──────────────────────────
# core.worker (Celery) — needs Redis at import time
sys.modules.setdefault("core.worker", MagicMock())

# tools.crawler — initialises ChromaDB collection at module level
sys.modules.setdefault("tools.crawler", MagicMock())

# tools.pm_tools — connects to Jira/Linear at import time
sys.modules.setdefault("tools.pm_tools", MagicMock())

# FastAPI routers — provide real APIRouter() so app.include_router() succeeds
for _router_mod in ["agents.terminal", "agents.spectre", "agents.git_automator"]:
    _mock = MagicMock()
    _mock.router = APIRouter()
    sys.modules.setdefault(_router_mod, _mock)

# ── Stable test identity (avoids filesystem access in all tests) ──────────────
os.environ.setdefault("ENGRAM_USER_ID", "test-user-uuid-0001")
