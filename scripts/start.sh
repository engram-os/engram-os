#!/bin/bash

GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

preflight_checks() {
  local errors=0

  printf "${CYAN}Running pre-flight checks...${NC}\n"

  # 1. Docker running?
  if ! docker info > /dev/null 2>&1; then
    printf "${RED}✗ Docker is not running. Start Docker Desktop first.${NC}\n"
    errors=$((errors + 1))
  else
    printf "${GREEN}✓ Docker is running${NC}\n"
  fi

  # 2. Ollama reachable?
  if ! curl -s --max-time 3 http://localhost:11434/ > /dev/null 2>&1; then
    printf "${RED}✗ Ollama is not running. Start it with: ollama serve${NC}\n"
    errors=$((errors + 1))
  else
    printf "${GREEN}✓ Ollama is reachable${NC}\n"
  fi

  # 3. .env file present?
  if [ ! -f .env ]; then
    printf "${RED}✗ .env file not found. Copy .env.example and fill in values.${NC}\n"
    errors=$((errors + 1))
  else
    printf "${GREEN}✓ .env file present${NC}\n"

    # 4. AUDIT_HMAC_SECRET set? (brain crashes at import if missing)
    if ! grep -q "^AUDIT_HMAC_SECRET=." .env; then
      printf "${RED}✗ AUDIT_HMAC_SECRET not set in .env.${NC}\n"
      printf "   Fix: echo \"AUDIT_HMAC_SECRET=\$(python3 -c 'import secrets; print(secrets.token_hex(32))')\" >> .env\n"
      errors=$((errors + 1))
    else
      printf "${GREEN}✓ AUDIT_HMAC_SECRET is set${NC}\n"
    fi
  fi

  # 5. Google OAuth token — warning only (graceful degradation without it)
  if [ ! -f credentials/token.json ]; then
    printf "${YELLOW}⚠ credentials/token.json missing — Google Calendar/Gmail features disabled.${NC}\n"
    printf "   Fix: python3 scripts/generate_token.py\n"
  else
    printf "${GREEN}✓ Google OAuth token present${NC}\n"
  fi

  # 6. Available memory — warning only, Linux only (macOS Docker runs in a VM)
  if [[ "$(uname)" != "Darwin" ]]; then
    free_mb=$(free -m | awk '/Mem:/{print $7}')
    if [ "$free_mb" -lt 2048 ]; then
      printf "${YELLOW}⚠ Low available memory: ${free_mb}MB free (2048MB recommended).${NC}\n"
    else
      printf "${GREEN}✓ Memory OK: ${free_mb}MB available${NC}\n"
    fi
  fi

  if [ "$errors" -gt 0 ]; then
    printf "\n${RED}Pre-flight failed with ${errors} error(s). Fix the above and retry.${NC}\n"
    exit 1
  fi

  printf "${GREEN}All checks passed.${NC}\n\n"
}

init_local_ai() {
  preflight_checks

  printf "${CYAN}Starting Engram...${NC}\n"
  IDENTITY_FILE="$HOME/.engram/identity.json"
  if [ -f "$IDENTITY_FILE" ]; then
    export ENGRAM_USER_ID=$(python3 -c "import json; print(json.load(open('$IDENTITY_FILE'))['user_id'])")
  else
    export ENGRAM_USER_ID=$(python3 -c "import uuid; print(str(uuid.uuid4()))")
    mkdir -p "$HOME/.engram"
    python3 -c "import json, datetime, os
data = {'user_id': '$ENGRAM_USER_ID', 'created_at': str(datetime.datetime.now()), 'machine': os.uname().nodename}
json.dump(data, open('$IDENTITY_FILE', 'w'), indent=2)"
    chmod 600 "$IDENTITY_FILE"
  fi
  printf "${GREEN}User identity: ${ENGRAM_USER_ID}${NC}\n"

  printf "${GREEN}Starting Docker Infrastructure...${NC}\n"

  mkdir -p data/logs

  docker-compose up -d

  run_processes() {
    local name=$1
    local script=$2
    local pid_file=".${name}_pid"
    local pid

    if [ "$name" == "ui" ]; then
        nohup python3 -m streamlit run "$script" > data/logs/"$name".log 2>&1 &
    else
        nohup python3 "$script" > data/logs/"$name".log 2>&1 &
    fi

    pid=$!
    
    echo $pid > "$pid_file"
    printf "Running $name (PID: $pid)\n"
  }

  run_processes browser_sync sensors/browser_sync.py
  run_processes ingestor sensors/ingestor.py
  run_processes ui interface/dashboard.py

  printf "${CYAN}SYSTEM ONLINE${NC}\n"
  printf "   - API:        http://localhost:8000\n"
  printf "   - Dashboard:  http://localhost:8501\n"
  printf "   - Agent:      Autonomous (Runs every 15 mins)\n"
  printf "   - Ingestor:   Watching 'data/inbox' folder\n"
  printf "\n"
  printf "To shut down, run: ./scripts/stop.sh\n"
}

init_local_ai