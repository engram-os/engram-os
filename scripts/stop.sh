#!/bin/bash

GREEN='\033[0;32m'
CYAN='\033[0;36m'
NC='\033[0m'

printf "${CYAN}Stopping Engram...${NC}\n"

printf "${GREEN}Stopping Docker Infrastructure...${NC}\n"
docker-compose down

cleanup_process() {
    local name=$1
    local pid_file=".${name}_pid"

    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        
        if kill -0 "$pid" 2>/dev/null; then
            kill "$pid"
            printf "   - Stopped $name (PID: $pid)\n"
        else
            printf "   - $name was not running (Stale PID)\n"
        fi
        
        rm "$pid_file"
    else
        printf "   - $name is already stopped.\n"
    fi
}

cleanup_process "browser_sync"
cleanup_process "ingestor"
cleanup_process "ui"

printf "${CYAN}SYSTEM OFFLINE${NC}\n"