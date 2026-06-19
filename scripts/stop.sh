#!/bin/bash

GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
NC='\033[0m'

printf "${CYAN}Stopping Engram...${NC}\n"

# ── 1. Stop sensor processes (they post to the brain — stop before Docker) ────

cleanup_process() {
    local name=$1
    local pid_file=".${name}_pid"

    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if kill -0 "$pid" 2>/dev/null; then
            kill "$pid"
            printf "   - Stopped $name (PID: $pid)\n"
        else
            printf "   - $name was not running (stale PID)\n"
        fi
        rm "$pid_file"
    else
        printf "   - $name is already stopped.\n"
    fi
}

cleanup_process "browser_sync"
cleanup_process "ingestor"

# ── 2. Stop Docker infrastructure ─────────────────────────────────────────────

printf "${GREEN}Stopping Docker infrastructure...${NC}\n"
docker-compose down

# ── 3. Back up Qdrant data volume ─────────────────────────────────────────────
# Run after docker-compose down so no containers have open file handles on the
# volume. The volume itself persists — docker-compose down never deletes volumes.

backup_qdrant() {
    local backup_dir="data/backups"
    mkdir -p "$backup_dir"

    if ! docker volume inspect qdrant_data > /dev/null 2>&1; then
        printf "${YELLOW}⚠  qdrant_data volume not found — skipping backup${NC}\n"
        return
    fi

    local timestamp
    timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_file="${backup_dir}/qdrant_${timestamp}.tar.gz"
    local abs_backup_dir
    abs_backup_dir="$(pwd)/${backup_dir}"

    printf "${CYAN}Backing up Qdrant data volume...${NC}\n"
    if docker run --rm \
        -v qdrant_data:/qdrant_data:ro \
        -v "${abs_backup_dir}:/backup" \
        alpine \
        tar czf "/backup/qdrant_${timestamp}.tar.gz" /qdrant_data 2>/dev/null; then
        printf "${GREEN}✓ Backup saved: ${backup_file}${NC}\n"
    else
        printf "${YELLOW}⚠  Backup failed (Docker not available or volume empty)${NC}\n"
        return
    fi

    # Rolling prune — keep only the last 7 days of backups to cap disk usage.
    local pruned
    pruned=$(find "$backup_dir" -name "qdrant_*.tar.gz" -mtime +7 -print -delete 2>/dev/null | wc -l | tr -d ' ')
    if [ "$pruned" -gt 0 ]; then
        printf "   Pruned $pruned backup(s) older than 7 days.\n"
    fi
}

backup_qdrant

printf "${CYAN}SYSTEM OFFLINE${NC}\n"
