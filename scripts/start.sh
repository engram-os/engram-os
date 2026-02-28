#!/bin/bash

GREEN='\033[0;32m'
CYAN='\033[0;36m'
NC='\033[0m'

init_local_ai() {
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