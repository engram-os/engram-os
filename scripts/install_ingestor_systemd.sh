#!/usr/bin/env bash
# install_ingestor_systemd.sh — Install the Engram file-watcher as a systemd user service (Linux).
#
# Usage:
#   chmod +x scripts/install_ingestor_systemd.sh
#   ./scripts/install_ingestor_systemd.sh
#
# To uninstall:
#   systemctl --user disable --now engram-ingestor
#   rm ~/.config/systemd/user/engram-ingestor.service
#   systemctl --user daemon-reload

set -euo pipefail

UNIT="engram-ingestor"
UNIT_DIR="$HOME/.config/systemd/user"
UNIT_PATH="$UNIT_DIR/$UNIT.service"

# Resolve project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Detect python
if [[ -x "$PROJECT_DIR/venv/bin/python" ]]; then
    PYTHON="$PROJECT_DIR/venv/bin/python"
elif command -v python3 &>/dev/null; then
    PYTHON="$(command -v python3)"
else
    echo "ERROR: No python3 found." >&2
    exit 1
fi

echo "Using Python: $PYTHON"
echo "Project dir:  $PROJECT_DIR"

mkdir -p "$UNIT_DIR"

cat > "$UNIT_PATH" <<UNIT
[Unit]
Description=Engram file-watcher ingestor
After=network.target

[Service]
Type=simple
WorkingDirectory=${PROJECT_DIR}
ExecStart=${PYTHON} ${PROJECT_DIR}/sensors/ingestor.py
Restart=on-failure
RestartSec=10s
Environment="PYTHONPATH=${PROJECT_DIR}:${PROJECT_DIR}/core"
Environment="INGEST_API_URL=http://localhost:8000/ingest"

# Forward stdout/stderr to journald — view with: journalctl --user -u engram-ingestor -f
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=default.target
UNIT

systemctl --user daemon-reload
systemctl --user enable --now "$UNIT"

echo ""
echo "Engram ingestor installed and started."
echo "  Status:  systemctl --user status $UNIT"
echo "  Logs:    journalctl --user -u $UNIT -f"
echo "  Remove:  systemctl --user disable --now $UNIT && rm $UNIT_PATH"
