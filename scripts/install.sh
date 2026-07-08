#!/usr/bin/env bash
# Engram OS one-command installer.
#
#   curl -fsSL https://raw.githubusercontent.com/engram-os/engram-os/main/scripts/install.sh | bash
#
# Checks prerequisites (Docker, Python, Ollama), pulls the two models,
# clones the repo (unless run from inside an existing checkout), then
# runs setup and start. Safe to re-run — every step is idempotent.
#
# Env overrides:
#   ENGRAM_DIR=/path        where to clone (default: ~/engram-os)
#   ENGRAM_INSTALL_DRY_RUN=1  print actions without executing them

set -euo pipefail

REPO_URL="https://github.com/engram-os/engram-os.git"
INSTALL_DIR="${ENGRAM_DIR:-$HOME/engram-os}"
DRY_RUN="${ENGRAM_INSTALL_DRY_RUN:-0}"
MODELS=("llama3.1:latest" "nomic-embed-text:latest")

info() { printf '\033[1;36m==>\033[0m %s\n' "$*"; }
ok()   { printf '\033[1;32m ✓ \033[0m %s\n' "$*"; }
fail() { printf '\033[1;31m ✗ \033[0m %s\n' "$*" >&2; exit 1; }
run()  { if [ "$DRY_RUN" = "1" ]; then echo "    [dry-run] $*"; else "$@"; fi; }

info "Engram OS installer"

# ── 1. Platform ──────────────────────────────────────────────────────────
case "$(uname -s)" in
  Darwin|Linux) ok "Platform: $(uname -s)" ;;
  *) fail "Engram runs on macOS or Linux. On Windows, use WSL2." ;;
esac

# ── 2. Docker ────────────────────────────────────────────────────────────
command -v docker >/dev/null 2>&1 \
  || fail "Docker is required. Install it: https://docs.docker.com/get-docker/"
docker info >/dev/null 2>&1 \
  || fail "Docker is installed but not running. Start Docker Desktop (or dockerd) and re-run."
docker compose version >/dev/null 2>&1 \
  || fail "Docker Compose v2 is required (included with Docker Desktop)."
ok "Docker + Compose"

# ── 3. Python 3.11+ ──────────────────────────────────────────────────────
command -v python3 >/dev/null 2>&1 \
  || fail "Python 3.11+ is required. Install it: https://www.python.org/"
python3 -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)' \
  || fail "Python 3.11+ required — found $(python3 --version 2>&1). Upgrade and re-run."
ok "$(python3 --version 2>&1)"

# ── 4. Ollama ────────────────────────────────────────────────────────────
if ! curl -s --max-time 3 http://localhost:11434/api/tags >/dev/null 2>&1; then
  fail "Ollama is not reachable at localhost:11434.
    Install it from https://ollama.com then make sure it's running, and re-run this script."
fi
ok "Ollama is running"

# ── 5. Models ────────────────────────────────────────────────────────────
tags="$(curl -s --max-time 5 http://localhost:11434/api/tags || true)"
for model in "${MODELS[@]}"; do
  if printf '%s' "$tags" | grep -q "\"$model\""; then
    ok "Model present: $model"
  else
    command -v ollama >/dev/null 2>&1 \
      || fail "Model $model is missing and the 'ollama' CLI isn't on PATH. Run: ollama pull $model"
    info "Pulling $model (one-time, a few GB)…"
    run ollama pull "$model"
  fi
done

# ── 6. Get the code ──────────────────────────────────────────────────────
if [ -f docker-compose.yml ] && grep -q "ai_os_api" docker-compose.yml 2>/dev/null; then
  INSTALL_DIR="$(pwd)"
  ok "Running inside an existing Engram checkout: $INSTALL_DIR"
elif [ -d "$INSTALL_DIR/.git" ]; then
  ok "Existing checkout found at $INSTALL_DIR — updating"
  run git -C "$INSTALL_DIR" pull --ff-only
else
  command -v git >/dev/null 2>&1 || fail "git is required to clone the repository."
  info "Cloning into $INSTALL_DIR"
  run git clone "$REPO_URL" "$INSTALL_DIR"
fi

# ── 7. Setup + launch ────────────────────────────────────────────────────
if [ "$DRY_RUN" = "1" ]; then
  echo "    [dry-run] cd $INSTALL_DIR && ./scripts/setup.sh && ./scripts/start.sh"
  info "Dry run complete — no changes made."
  exit 0
fi

cd "$INSTALL_DIR"
info "Running one-time setup"
bash scripts/setup.sh
info "Starting Engram"
bash scripts/start.sh

echo
ok "Engram is up."
echo "    Dashboard  → http://localhost:8501"
echo "    API        → http://localhost:8000"
