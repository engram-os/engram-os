#!/bin/bash
# scripts/setup.sh — Engram OS one-time setup
# Run once before scripts/start.sh. Safe to re-run (idempotent — skips steps already done).

set -e

GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BOLD='\033[1m'
NC='\033[0m'

pass()    { printf "${GREEN}✓ $1${NC}\n"; }
warn()    { printf "${YELLOW}⚠  $1${NC}\n"; }
fail()    { printf "${RED}✗ $1${NC}\n"; exit 1; }
info()    { printf "   ${CYAN}→ $1${NC}\n"; }
section() { printf "\n${BOLD}── $1${NC}\n"; }

# ── 1. Python ─────────────────────────────────────────────────────────────────
section "Python"

PYTHON=""
for candidate in python3.11 python3; do
  if command -v "$candidate" &>/dev/null; then
    if "$candidate" -c 'import sys; exit(0 if sys.version_info >= (3,11) else 1)' 2>/dev/null; then
      PYTHON="$candidate"
      break
    fi
  fi
done

if [ -z "$PYTHON" ]; then
  fail "Python 3.11+ not found. Install it from https://www.python.org/ and retry."
fi
pass "Python found: $($PYTHON --version)"

# ── 2. Python venv ────────────────────────────────────────────────────────────
section "Python Environment"

if [ -f venv/bin/python ]; then
  pass "venv already exists — skipping creation"
else
  printf "Creating virtual environment...\n"
  "$PYTHON" -m venv venv
  pass "venv created"
fi

printf "Installing dependencies from config/requirements.txt...\n"
venv/bin/pip install --quiet -r config/requirements.txt
pass "Dependencies installed"

# ── 3. Environment file ───────────────────────────────────────────────────────
section "Environment Configuration"

if [ -f .env ]; then
  pass ".env already exists — skipping copy"
else
  cp .env.example .env
  pass ".env created from .env.example"
fi

# Helper: replace an empty KEY= line in .env with KEY=value
# Uses a temp file for portability across macOS (BSD sed) and Linux (GNU sed).
set_env_var() {
  local key=$1
  local value=$2
  if grep -q "^${key}=$" .env; then
    # Key present but empty — fill it in
    tmp=$(mktemp)
    sed "s|^${key}=$|${key}=${value}|" .env > "$tmp" && mv "$tmp" .env
  elif ! grep -q "^${key}=" .env; then
    # Key absent entirely — append it
    echo "${key}=${value}" >> .env
  fi
}

# Helper: check if a key has a non-empty value in .env
# Works on both macOS (BSD grep) and Linux (GNU grep).
env_is_set() {
  local key=$1
  local val
  val=$(grep "^${key}=" .env 2>/dev/null | cut -d= -f2-)
  [ -n "$val" ]
}

# ENGRAM_ENCRYPTION_KEY
# Fernet key — AES-128 used to encrypt all memory payloads before they reach Qdrant.
# Generated locally by Python's cryptography library using the OS CSPRNG (/dev/urandom).
if env_is_set "ENGRAM_ENCRYPTION_KEY"; then
  pass "ENGRAM_ENCRYPTION_KEY already set — skipping"
else
  ENC_KEY=$(venv/bin/python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
  set_env_var "ENGRAM_ENCRYPTION_KEY" "$ENC_KEY"
  pass "ENGRAM_ENCRYPTION_KEY generated"
  info "Encrypts all memory stored in Qdrant. Generated locally — nothing transmitted externally."
fi

# AUDIT_HMAC_SECRET
# 256-bit random hex string — signs each audit log entry to form a tamper-evident chain.
# Generated locally using Python's secrets module (backed by OS CSPRNG).
if env_is_set "AUDIT_HMAC_SECRET"; then
  pass "AUDIT_HMAC_SECRET already set — skipping"
else
  HMAC_SECRET=$(venv/bin/python -c "import secrets; print(secrets.token_hex(32))")
  set_env_var "AUDIT_HMAC_SECRET" "$HMAC_SECRET"
  pass "AUDIT_HMAC_SECRET generated"
  info "Signs the audit log chain. Generated locally — nothing transmitted externally."
fi

# ENGRAM_USER_ID
# Pins all Docker containers (brain, worker, beat) to the same user UUID.
# Without this, each container generates its own UUID and Qdrant filters return empty results.
if env_is_set "ENGRAM_USER_ID"; then
  pass "ENGRAM_USER_ID already set — skipping"
else
  USER_UUID=$(venv/bin/python -c "import uuid; print(str(uuid.uuid4()))")
  set_env_var "ENGRAM_USER_ID" "$USER_UUID"
  pass "ENGRAM_USER_ID generated"
  info "Pins all containers to the same user identity so Qdrant queries return consistent results."
fi

# ── 4. Required directories ───────────────────────────────────────────────────
section "Directories"

for dir in data/inbox data/inbox/processed data/dbs data/logs credentials; do
  if [ -d "$dir" ]; then
    pass "Exists:  $dir"
  else
    mkdir -p "$dir"
    pass "Created: $dir"
  fi
done

# ── 5. Summary ────────────────────────────────────────────────────────────────
printf "\n${BOLD}══ Setup Complete ══════════════════════════════════${NC}\n\n"
printf "${GREEN}Your environment is ready.${NC}\n\n"
printf "Optional next steps:\n"
printf "  ${CYAN}ENGRAM_API_KEY${NC}  — set in .env to enable API authentication (production)\n"
printf "  ${CYAN}Google OAuth${NC}    — place credentials.json in credentials/ and run:\n"
printf "                    venv/bin/python scripts/generate_token.py\n"
printf "  ${CYAN}PM integrations${NC} — add LINEAR_KEY / JIRA_* to .env for Daily Briefing\n"
printf "\n"
printf "When ready:\n"
printf "  ${GREEN}./scripts/start.sh${NC}\n\n"
printf "${YELLOW}Note on secrets:${NC} ENGRAM_ENCRYPTION_KEY and AUDIT_HMAC_SECRET were generated\n"
printf "locally on this machine using your OS's built-in secure random generator.\n"
printf "They are stored only in .env and never transmitted externally.\n\n"
