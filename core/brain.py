import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from agents.tasks import _fan_out_calendar, _fan_out_email
from core.auth import LOCAL_USER_ID
from core.deps import client  # noqa: F401 — re-exported so test patches on core.brain.client still resolve
from core.user_registry import bootstrap_admin
from core.matter_registry import bootstrap_default_matter

from agents.terminal import router as terminal_router
from agents.spectre import router as spectre_router
from agents.git_automator import router as git_router

from api.audit import router as audit_router
from api.users import router as users_router
from api.matters import router as matters_router
from api.agents import router as agents_router
from api.knowledge import router as knowledge_router
from api.memory import router as memory_router
from api.chat import router as chat_router
from api.openai_compat import router as openai_router
from api.mcp_server import mcp

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

_scheduler = AsyncIOScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    _scheduler.add_job(_fan_out_calendar, "interval", minutes=15, max_instances=1, misfire_grace_time=60)
    _scheduler.add_job(_fan_out_email, "interval", hours=1, max_instances=1, misfire_grace_time=120)
    _scheduler.start()
    logger.info("APScheduler started: calendar (15 min), email (60 min)")
    yield
    _scheduler.shutdown(wait=False)
    logger.info("APScheduler stopped.")


app = FastAPI(title="Engram OS Brain", docs_url=None, redoc_url=None, lifespan=lifespan)

ALLOWED_ORIGINS = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:8501,http://127.0.0.1:8501,http://localhost:3000,http://127.0.0.1:3000",
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Bootstrap (idempotent) ────────────────────────────────────────────────────
_ENGRAM_API_KEY = os.getenv("ENGRAM_API_KEY")
if _ENGRAM_API_KEY:
    bootstrap_admin(LOCAL_USER_ID, _ENGRAM_API_KEY)
    bootstrap_default_matter(LOCAL_USER_ID)

# ── Legacy agent routers ──────────────────────────────────────────────────────
app.include_router(terminal_router)
app.include_router(spectre_router)
app.include_router(git_router)

# ── API routers ───────────────────────────────────────────────────────────────
app.include_router(audit_router)
app.include_router(users_router)
app.include_router(matters_router)
app.include_router(agents_router)
app.include_router(knowledge_router)
app.include_router(memory_router)
app.include_router(chat_router)
app.include_router(openai_router)

app.mount("/mcp", mcp.sse_app())


@app.get("/")
def read_root():
    return {"status": "Engram is Online", "version": "1.0.0"}
