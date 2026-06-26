"""
Test suite bootstrap — stubs heavy third-party and project modules before any
project code is imported.  This file is loaded by pytest before test collection
begins, so all sys.modules entries below are in place before the first import.
"""
import os
import sys
from unittest.mock import MagicMock
from fastapi import APIRouter


# ── MCP stub — FastMCP.tool() / .resource() must be identity decorators so
# tool functions remain directly callable in tests. A plain MagicMock would
# wrap them in another MagicMock and break direct invocation.
class _FakeFastMCP:
    def __init__(self, name: str = ""):
        self.name = name

    def tool(self):
        def decorator(fn): return fn
        return decorator

    def resource(self, pattern: str):
        def decorator(fn): return fn
        return decorator

    def sse_app(self):
        return MagicMock()


_fastmcp_mod = MagicMock()
_fastmcp_mod.FastMCP = _FakeFastMCP
sys.modules["mcp"] = MagicMock()
sys.modules["mcp.server"] = MagicMock()
sys.modules["mcp.server.fastmcp"] = _fastmcp_mod

# ── Third-party packages that connect to external services at import time ─────
for _mod in [
    "qdrant_client", "qdrant_client.http", "qdrant_client.http.models",
    "ollama",
    "apscheduler", "apscheduler.schedulers", "apscheduler.schedulers.asyncio",
    "google.auth", "google.auth.transport", "google.auth.transport.requests",
    "google.oauth2", "google.oauth2.credentials",
    "google_auth_oauthlib", "google_auth_oauthlib.flow",
    "googleapiclient", "googleapiclient.discovery",
    "streamlit",
    "jira",
    "bs4",
    "pypdf",
    "dateutil", "dateutil.parser",
]:
    sys.modules.setdefault(_mod, MagicMock())

# ── Project modules with heavy runtime side-effects ──────────────────────────
# tools.crawler — connects to Qdrant at module level (_ensure_doc_collection)
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

# ── Audit log secret (required at agents.logger import time) ──────────────────
os.environ.setdefault("AUDIT_HMAC_SECRET", "test-audit-hmac-secret-0000000000000000")

# ── API key: empty string activates dev-mode passthrough in get_current_user ──
os.environ.setdefault("ENGRAM_API_KEY", "")
