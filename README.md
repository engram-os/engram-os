<div align="center">

  <img src="screenshots/Engram.png" alt="Engram Logo" width="100" height="100" />

  # Engram OS
  **Your AI, On Your Device. Complete Privacy. Complete Control.**

  [![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
  [![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=flat-square&logo=docker&logoColor=white)](https://www.docker.com/)
  [![Llama 3.1](https://img.shields.io/badge/Model-Llama_3.1-424242?style=flat-square&logo=ollama&logoColor=white)](https://ollama.com/)
  [![Encrypted](https://img.shields.io/badge/Memory-AES--128_Encrypted-4CAF50?style=flat-square&logo=letsencrypt&logoColor=white)]()
  [![Multi-User](https://img.shields.io/badge/Auth-Multi--User_+_Roles-9C27B0?style=flat-square&logo=shield&logoColor=white)]()
  [![Audit Trail](https://img.shields.io/badge/Audit-HMAC_Chain-FF5722?style=flat-square&logo=databricks&logoColor=white)]()
  [![License](https://img.shields.io/badge/License-AGPL_3.0-F7DF1E?style=flat-square)](https://opensource.org/license/agpl-v3)

</div>

**Engram OS** is a local-first, privacy-grade AI Operating System built to run entirely on your hardware via Docker — **zero data egress, ever**. It features encrypted vector memory, a tamper-evident audit trail, role-based multi-user access, a real-time autonomous agent nervous system, and a dual-pipeline RAG architecture — all powered by Llama 3.1 running locally via Ollama.

---

## Quick Start

**Prerequisites:**
- [Docker + Docker Compose](https://docs.docker.com/get-docker/)
- [Ollama](https://ollama.com/) running on the host at port `11434`
- Ollama models pulled: `llama3.1:latest` and `nomic-embed-text:latest`

```bash
# 1. Clone
git clone https://github.com/engram-os/engram-os.git && cd engram-os

# 2. Set up environment
cp .env.example .env
# Edit .env — generate your encryption key:
#   python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# 3. Launch everything
chmod +x scripts/start.sh && ./scripts/start.sh
```

**Services after startup:**

| Service | URL | Description |
|---|---|---|
| Dashboard (UI) | `http://localhost:8501` | Streamlit command center |
| Brain (API) | `http://localhost:8000` | FastAPI orchestrator |
| Qdrant (dev only) | `http://localhost:6334/dashboard` | Vector DB explorer |

> Qdrant's HTTP port is only exposed in dev mode via `docker-compose.override.yml`. It is not accessible in the default production stack.

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                          ENGRAM OS — Docker Network                 │
│                                                                     │
│ HOST PROCESSES (bare nohup)                   DOCKER CONTAINERS     │
│ ┌────────────────────────┐                                          │
│ │  sensors/ingestor.py   │──POST /ingest──▶ ┌─────────────────────┐ │
│ │  (polls data/inbox/)   │                  │   BRAIN  :8000      │ │
│ └────────────────────────┘                  │   core/brain.py     │ │
│  ┌────────────────────────┐──POST /ingest──▶│   FastAPI           │ │
│  │ sensors/browser_sync   │                 └────────┬────────────┘ │ 
│  │ (Chrome/Brave history) │                          │              │ 
│  └────────────────────────┘         ┌────────────────┼─────────┐    │
│                                     │                │         │    │
│                              ┌──────▼──────┐  ┌──────▼───┐ ┌───▼──┐ │
│  ┌────────────────────────┐  │  Encrypted  │  │  Audit   │ │Ollama│ │
│  │  DASHBOARD  :8501      │  │  Memory     │  │  Writer  │ │:11434│ │
│  │  interface/dashboard   │  │  Client     │  │  (socket)│ │(host)│ │
│  │  Streamlit             │  │  AES-128    │  │  HMAC    │ └──────┘ │
│  └───────────┬────────────┘  └──────┬──────┘  └──────────┘          │
│              │ GET /api/audit/logs  │                               │
│              │◀─────────────────────┘            ┌───────────────┐  │
│              │                           ┌──────▶│    QDRANT     │  │
│              └──────────────────────────▶│       │  second_brain │  │ 
│                    HTTP (Brain API)      │       │  768-dim vecs │  │
│                                          │       └───────────────┘  │
│  ┌────────────────────────────────────┐  │       ┌───────────────┐  │
│  │  CELERY WORKER + BEAT              │  └──────▶│   ChromaDB    │  │
│  │  agents/tasks.py                   │          │  doc_knowledge│  │
│  │  CalendarAgent (15 min)            │          │  384-dim vecs │  │
│  │  EmailAgent    (60 min)            │          └───────────────┘  │
│  └────────────────────────────────────┘                             │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  MESSAGE BUS: Redis  ◀──────────────── Celery tasks          │   │
│  └──────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Project Structure

```
engram-os/
│
├── core/                          # The Brain
│   ├── brain.py                   # FastAPI orchestrator — all main endpoints
│   ├── memory_client.py           # EncryptedMemoryClient (Fernet AES-128 wrapper)
│   ├── network_gateway.py         # Centralized outbound HTTP — SSRF protection
│   ├── classification_engine.py   # PHI / Confidential / Internal / Public labels
│   ├── sanitizer.py               # PII stripping above classification threshold
│   ├── user_registry.py           # Multi-user SQLite store, roles, SHA256 key hash
│   ├── matter_registry.py         # Matter registry + user_matter_access table
│   ├── identity.py                # Persistent local UUID (~/.engram/identity.json)
│   ├── worker.py                  # Celery app config + beat schedule
│   └── jarvis.py                  # Autonomous agent logic
│
├── agents/                        # The Nervous System
│   ├── tasks.py                   # Celery tasks: CalendarAgent, EmailAgent
│   ├── logger.py                  # Agent activity log (routes via audit socket)
│   ├── tools.py                   # Google Calendar API integration
│   ├── gmail_tools.py             # Gmail OAuth integration
│   ├── auth.py                    # Per-user Google credentials resolver
│   ├── terminal.py                # Terminal Genie router (mounted in brain)
│   ├── spectre.py                 # VS Code Spectre router (mounted in brain)
│   └── git_automator.py           # Git automation router (mounted in brain)
│
├── audit_writer/                  # Tamper-Evident Audit Trail
│   ├── server.py                  # Unix socket server — sole writer to audit.db
│   └── __init__.py
│
├── interface/
│   └── dashboard.py               # Streamlit command center (dark/light mode)
│
├── sensors/                       # Input Watchdogs (host processes)
│   ├── ingestor.py                # Polls data/inbox/ every 5s, extracts + POSTs
│   └── browser_sync.py            # Snapshots Chrome/Brave history
│
├── tools/
│   ├── crawler.py                 # DocSpider BFS crawler → ChromaDB
│   └── pm_tools.py                # Jira / Linear integration
│
├── cli/
│   └── genie.py                   # Terminal Genie shell helper
│
├── scripts/
│   ├── start.sh                   # Full system startup
│   ├── stop.sh                    # Graceful shutdown
│   ├── seed_demo.py               # 55-point demo dataset seeder
│   └── reseed_matters.py          # Re-seeds points with correct matter_id UUIDs
│
├── config/
│   ├── Dockerfile
│   └── requirements.txt           # Pinned direct dependencies
│
├── tests/                         # 91 tests, all passing
│
├── data/
│   ├── inbox/                     # Drop files here for auto-ingestion
│   ├── inbox/processed/           # Ingestor moves files here after ingestion
│   ├── demo_files/                # Ready-to-drop demo documents
│   └── dbs/                       # SQLite stores (users, matters, agent activity)
│
├── docker-compose.yml             # Production stack
├── docker-compose.override.yml    # Dev overrides (Qdrant port exposed)
└── .env.example                   # Required environment variables
```

---

## Docker Services

```
                  ┌───────────────────────────────────────────────────┐
                  │        Docker Compose  ── ai_os_net bridge        │
                  │                                                   │
                  │   ┌──────────────┐      ┌──────────────────────┐  │
                  │   │  ai_os_vault │      │    ai_os_api         │  │
                  │   │  Qdrant      │◀─────│    FastAPI :8000     │  │
                  │   │  Vector DB   │      │    core/brain.py     │  │
                  │   └──────────────┘      └──────────┬───────────┘  │
                  │                                    │              │
                  │   ┌──────────────┐      ┌──────────▼───────────┐  │
                  │   │  engram_redis│      │  ai_os_dashboard     │  │
                  │   │  Redis :6379 │◀──── │  Streamlit :8501     │  │
                  │   │  Task broker │      └──────────────────────┘  │
                  │   └──────┬───────┘                                │
                  │          │              ┌──────────────────────┐  │
                  │   ┌──────▼───────┐      │  engram_audit        │  │
                  │   │  engram_     │      │  Unix socket server  │  │
                  │   │  worker      │─────▶│  HMAC audit chain    │  │
                  │   │  Celery      │      │  128MB / 0.25 CPU    │  │
                  │   └──────────────┘      └──────────────────────┘  │
                  │   ┌──────────────┐                                │
                  │   │  engram_beat │                                │
                  │   │  Celery Beat │                                │
                  │   │  Scheduler   │                                │
                  │   └──────────────┘                                │
                  └───────────────────────────────────────────────────┘
```

| Container | Image | Role | Memory Limit |
|---|---|---|---|
| `ai_os_vault` | `qdrant/qdrant` | Vector database | 2 GB |
| `ai_os_api` | local build | FastAPI brain, main API | 1 GB |
| `ai_os_dashboard` | local build | Streamlit UI | 512 MB |
| `engram_audit` | local build | Sole audit DB writer (Unix socket) | 128 MB |
| `engram_redis` | `redis:7-alpine` | Celery message broker | 256 MB |
| `engram_worker` | local build | Celery background agent executor | 2 GB |
| `engram_beat` | local build | Celery beat scheduler | 256 MB |

---

## Security Architecture

Every piece of data passes through a five-layer security stack before it is ever stored.

```
  Incoming text (chat / ingest / add-memory)
                    │
                    ▼
  ┌───────────────────────────────────────┐
  │  1. Bearer Token Auth                 │
  │     ENGRAM_API_KEY (SHA-256 hashed)   │
  │     get_current_user() dependency     │
  │     Roles: admin | user               │
  └──────────────────┬────────────────────┘
                     │
                     ▼
  ┌───────────────────────────────────────┐
  │  2. Classification Engine             │
  │     PHI > Confidential >              │
  │     Internal > Public                 │
  │     Regex + LLM scoring               │
  └──────────────────┬────────────────────┘
                     │
                     ▼
  ┌───────────────────────────────────────┐
  │  3. Sanitizer                         │
  │     Strips PII fields above           │
  │     configured threshold              │
  └──────────────────┬────────────────────┘
                     │
                     ▼
  ┌───────────────────────────────────────┐
  │  4. Network Gateway                   │
  │     All outbound HTTP goes here       │
  │     Whitelisted destinations only     │
  │     Blocks SSRF / private IPs /       │
  │     cloud metadata endpoints          │
  └──────────────────┬────────────────────┘
                     │
                     ▼
  ┌───────────────────────────────────────┐
  │  5. EncryptedMemoryClient             │
  │     Fernet AES-128-CBC + HMAC-SHA256  │
  │     Plaintext (filterable):           │
  │       user_id, matter_id, type,       │
  │       classification, status          │
  │     Encrypted (everything else):      │
  │       memory, embed_text, created_at, │
  │       document_keys, ...              │
  └───────────────────────────────────────┘
```

### Encryption Key Resolution

```
ENGRAM_ENCRYPTION_KEY (env var)
        │  if not set
        ▼
~/.engram/vault.key   ← auto-generated on first run (chmod 0o600)
```

> **Critical:** `ENGRAM_ENCRYPTION_KEY` must be set to the **same value** in all containers (`os_layer`, `celery_worker`). Without it, each container auto-generates a divergent key and cannot decrypt the other's writes.

---

## Multi-User & Matter Architecture

Engram supports isolated workspaces called **Matters** — each with its own memory namespace, access control, and lifecycle.

```
Organization
└── Users
    ├── admin  (role: admin)
    │     └── can manage users, view audit logs, delete any memory
    │
    └── user   (role: user)
          ├── Matter A  (e.g. "Smith v. Aetna")
          │     ├── memory: claim denial details
          │     ├── memory: appeal letter draft
          │     └── memory: adjuster notes
          │
          └── Matter B  (e.g. "Doe — Cigna MRI Auth")
                ├── memory: PA authorization
                └── memory: calendar reminder
```

| Concept | Storage | Description |
|---|---|---|
| **User** | `data/dbs/users.db` | Display name, role, SHA-256 hashed API key |
| **Matter** | `data/dbs/matter_registry.db` | Named workspace (`active` / `closed` / `archived`) |
| **Access** | `user_matter_access` table | Many-to-many: which users can access which matters |
| **Memory** | Qdrant vector points | Each point stores `user_id` + `matter_id` as plaintext filterable fields |

**API auth flow:**
- Dev mode: `ENGRAM_API_KEY` unset → all requests pass as a synthetic admin user (local dev only)
- Production: Bearer token in `Authorization` header; `bootstrap_admin()` seeds the first admin on startup

---

## Tamper-Evident Audit Trail

The audit system uses a **sole-writer architecture** to guarantee log integrity. Only one process ever writes to `audit.db` — the `engram_audit` container.

```
  agents/logger.py          audit_writer/server.py
  (any container)                  │
        │                          │  sole owner of
        │  Unix socket IPC         │  audit_data volume
        │  /tmp/audit/audit.sock   │
        │─────── {"type": "log", ...} ──────────▶│
        │◀────── {"ok": true} ────────────────── │
        │                                        │
        │  message types:                        │  SQLite: /audit/audit.db
        │    log    → append new event           │  each row: timestamp, action,
        │    verify → check HMAC chain           │  user_id, details, HMAC
        │    recent → fetch last N events        │  prev_hash (chain link)
```

- Every audit record is chained: `HMAC(prev_hash + current_event)` — tampering any row breaks all subsequent hashes
- `GET /api/audit/logs` (admin only) — brain proxies to audit_writer via socket
- Dashboard activity feed reads from this endpoint — no direct DB access from UI

---

## Memory Architecture — Dual Vector Store

```
         ┌────────────────────────────────────────────────────────┐
         │                  Memory Ingestion                      │
         │                                                        │
         │  data/inbox/  ──▶  ingestor.py                         │
         │    (file drop)       │                                 │
         │                      ├─ extract_document_keys()        │
         │                      │   9 regex patterns:             │
         │                      │   insurer, claim_number,        │
         │                      │   auth_number, patient,         │
         │                      │   dos, cpt_code, icd10, ...     │
         │                      │                                 │
         │                      ├─ embed_text = key summary string│
         │                      │   (NOT full body — prevents     │
         │                      │    vector collapse on templates)│
         │                      │                                 │
         │                      └─▶  POST /ingest  ──▶  Qdrant    │
         └────────────────────────────────────────────────────────┘

  ┌──────────────────────────────┐    ┌──────────────────────────────┐
  │  Qdrant  (second_brain)      │    │  ChromaDB  (doc_knowledge)   │
  │                              │    │                              │
  │  Personal memory             │    │  External documentation      │
  │  nomic-embed-text (768-dim)  │    │  all-MiniLM-L6-v2 (384-dim)  │
  │  Encrypted at rest           │    │  Plain text (public docs)    │
  │  Filtered by user_id +       │    │  Populated via DocSpider     │
  │  matter_id                   │    │  crawler (BFS, BeautifulSoup)│
  │                              │    │                              │
  │  Used by: /chat, /ingest,    │    │  Used by: /api/docs/ingest   │
  │  /search, /add-memory,       │    │  /api/docs/query             │
  │  agents/tasks.py             │    │                              │
  └──────────────────────────────┘    └──────────────────────────────┘
```

**Deduplication rules by content type:**

| `type` | Dedup behaviour | point_id strategy |
|---|---|---|
| `file_ingest` | **Skipped** — intentional file drops always stored | `SHA256(user_id:claim_number)` — idempotent re-ingest |
| `raw_ingestion` | Cosine similarity threshold `0.97` | Content hash |
| `browsing_event` | Cosine similarity threshold `0.97` | Content hash |

---

## Autonomous Agents

Agents run on a heartbeat schedule via Celery Beat. Fan-out tasks enumerate all active users and dispatch per-user sub-tasks.

```
  Celery Beat (every N minutes)
        │
        ├─▶  fan_out_calendar  (every 15 min)
        │         │
        │         └─▶  run_calendar_agent(user_id, matter_id)  ×  each user
        │                   │
        │                   ├─ scroll Qdrant for unprocessed memories
        │                   ├─ LLM classifies: action = "schedule" | "none"
        │                   ├─ if "schedule" → Google Calendar API → create event
        │                   └─ mark memory status = "processed"
        │
        └─▶  fan_out_email  (every 60 min)
                  │
                  └─▶  run_email_agent(user_id)  ×  each user
                            │
                            ├─ Gmail OAuth → fetch unread threads
                            ├─ filter newsletters / spam
                            └─ LLM drafts reply → save to Drafts
```

**Calendar Agent trigger rules:**
- Fires on: `"Schedule a reminder"`, `"Remind me to"`, `"Book a slot"` — explicit scheduling intent only
- General facts (`"PA expires April 12"`) → `action: "none"` — no calendar event created

---

### Terminal Genie

Engram lives in your shell. When a command fails, the Genie intercepts.

```bash
$ git statsu
git: 'statsu' is not a git command.
$ ??
Genie is thinking...
Suggested Fix: git status
Run this command? [Y/n]
```

---

### Spectre (VS Code Extension)

A privacy-first AI pair programmer. Selected code is sent to your local Docker API — nothing leaves your machine.

- **Trigger:** Command Palette → `Spectre: Ask`
- **Capabilities:** Explain logic, find bugs, suggest refactors
- **Privacy:** All inference via Llama 3.1 on your GPU/CPU

---

### Git Automator

```bash
$ g-commit                        $ g-pr
Engram is reading your changes... Writing PR description...
─────────────────────────────     ─────────────────────────────
feat: Add validation logic to     ## Summary
  user signup flow                - Add input validation to signup
                                  - Guard against null email field
Apply this commit? [Y/n]          - Return 422 on malformed input
```

**Security Sentinel:** Pre-flight scans `git diff` for leaked secrets (AWS keys, tokens, credentials) before any push.

---

### Knowledge Base (DocSpider)

Turns Engram into a domain expert by ingesting external documentation into ChromaDB.

```
POST /api/docs/ingest  { "url": "https://flask.palletsprojects.com/" }
          │
          ▼
   DocSpider (BFS crawler)
          │
   BeautifulSoup parser
   ├─ separates code blocks from prose
   └─ generates embeddings locally (all-MiniLM-L6-v2)
          │
          ▼
      ChromaDB  (doc_knowledge collection)
          │
          ▼
POST /api/docs/query  →  RAG-grounded answers from the actual docs
```

---

### Daily Briefing & PM Sync

Aggregates tasks from Linear and Jira into a prioritized executive summary.

```
LINEAR_KEY + JIRA credentials  ──▶  pm_tools.py
                                         │
                                    normalize tickets
                                         │
                                    Llama 3.1 summary
                                         │
                                    Dashboard widget
                                    "You have 3 critical bugs today,
                                     focused on the Auth API"
```

**Configure in `.env`:**
```env
LINEAR_KEY=lin_api_...
JIRA_URL=https://yourcompany.atlassian.net
JIRA_EMAIL=me@company.com
JIRA_TOKEN=ATATT3...
```

---

## Data Ingestion

Drop any `.pdf`, `.txt`, `.md`, `.py`, `.js`, `.csv`, or `.json` file into `data/inbox/`. The ingestor daemon picks it up within 5 seconds:

```
data/inbox/
    my_denial.pdf
         │
         ▼  (ingestor.py — polls every 5s)
    extract text (pypdf / plain read)
         │
    extract_document_keys()
    ├── insurer, claim_number, auth_number
    ├── patient, date_of_service, cpt_code
    └── icd10, denial_code, reference
         │
    POST /ingest  (embed_text = key summary)
         │
    EncryptedMemoryClient.write() → Qdrant
         │
    data/inbox/processed/my_denial.pdf
```

---

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `ENGRAM_ENCRYPTION_KEY` | **Yes** | Base64 Fernet key — must be identical across all containers |
| `ENGRAM_API_KEY` | Yes (prod) | Bearer token for API auth; unset = dev mode (no auth) |
| `AUDIT_HMAC_SECRET` | Yes (prod) | HMAC secret for audit chain integrity |
| `ENGRAM_USER_ID` | **Yes** | Pin all containers to same user UUID (prevents Qdrant filter misses) |
| `OLLAMA_HOST` | No | Default: `http://host.docker.internal:11434` |
| `QDRANT_HOST` | No | Default: `qdrant` (Docker service name) |
| `CELERY_BROKER_URL` | No | Default: `redis://localhost:6379/0` |
| `INGEST_API_URL` | No | Default: `http://localhost:8000/ingest` |
| `LINEAR_KEY` | No | Activates Daily Briefing (Linear) |
| `JIRA_URL` / `JIRA_EMAIL` / `JIRA_TOKEN` | No | Activates Daily Briefing (Jira) |

**Generate your encryption key:**
```bash
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

---

## Google OAuth Setup

```
credentials/
├── credentials.json   ← Google OAuth client credentials (download from Google Console)
└── token.json         ← Generated OAuth token (run once to create)

python3 scripts/generate_token.py
```

Both files are volume-mounted into the `os_layer` and `celery_worker` containers.

---

## Running Components Individually

```bash
# FastAPI brain
uvicorn core.brain:app --host 0.0.0.0 --port 8000 --reload

# Streamlit dashboard
python3 -m streamlit run interface/dashboard.py

# Celery worker
celery -A core.worker.celery_app worker --loglevel=info

# Celery beat scheduler
celery -A core.worker.celery_app beat --loglevel=info

# File ingestor (host process — watches data/inbox/)
PYTHONPATH=$(pwd) venv/bin/python sensors/ingestor.py

# Seed demo data (medical billing, 55 memory points)
PYTHONPATH=core venv/bin/python scripts/seed_demo.py
```

---

## Test Suite

```bash
pytest tests/ -v
# 91 tests, all passing
```

Key test modules:

| Module | What it tests |
|---|---|
| `tests/test_memory_client.py` | Encrypt/decrypt round-trip, PLAINTEXT_KEYS, legacy compat, vault.key persistence |
| `tests/test_critical_paths.py` | Core API endpoints: /chat, /ingest, /search, /add-memory |
| `tests/test_multiuser.py` | User registry, matter isolation, role-based access |
| `tests/test_deletion.py` | Single + batch memory deletion, 403/404 guards |
| `tests/test_tools.py` | Calendar event creation, midnight edge case, all-day vs timed events |

---

## Privacy & Security

- **Local inference** — all LLM calls go to Ollama on your machine. No text reaches OpenAI or Anthropic.
- **Encrypted at rest** — Qdrant vectors and payloads encrypted with Fernet AES-128 before storage.
- **SSRF protection** — `NetworkGateway` validates every outbound HTTP call against a whitelist; private IP ranges and cloud metadata endpoints are blocked.
- **Tamper-evident logs** — HMAC chain on audit.db; any modification to a historical record breaks verification.
- **Qdrant not exposed** — port `6333` is not in the production compose file; only accessible via dev override.
- **OAuth credentials** — your personal Google OAuth token; Engram never proxies auth through any third-party.

---

## Contributing

We welcome contributions! Please see [`CONTRIBUTING.md`](CONTRIBUTING.md) for details on how to set up the dev environment.

## License

This project is licensed under the AGPL-3.0 License — see the [LICENSE](LICENSE) file for details.
