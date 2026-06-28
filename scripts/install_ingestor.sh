#!/usr/bin/env bash
# install_ingestor.sh — Install the Engram file-watcher as a macOS launchd agent.
#
# The agent auto-starts on login and restarts automatically if it crashes.
# Logs go to ~/Library/Logs/engram_ingestor.{out,err}.log
#
# Usage:
#   chmod +x scripts/install_ingestor.sh
#   ./scripts/install_ingestor.sh
#
# To uninstall:
#   ./scripts/uninstall_ingestor.sh

set -euo pipefail

LABEL="com.engram.ingestor"
PLIST_DIR="$HOME/Library/LaunchAgents"
PLIST_PATH="$PLIST_DIR/$LABEL.plist"
LOG_DIR="$HOME/Library/Logs"

# Resolve project root (one level above this script)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Detect python — prefer venv, fall back to system python3
if [[ -x "$PROJECT_DIR/venv/bin/python" ]]; then
    PYTHON="$PROJECT_DIR/venv/bin/python"
elif command -v python3 &>/dev/null; then
    PYTHON="$(command -v python3)"
else
    echo "ERROR: No python3 found. Install Python 3.11+ first." >&2
    exit 1
fi

echo "Using Python: $PYTHON"
echo "Project dir:  $PROJECT_DIR"

# Unload existing agent if present (suppress error if not loaded)
launchctl unload "$PLIST_PATH" 2>/dev/null || true

mkdir -p "$PLIST_DIR" "$LOG_DIR"

cat > "$PLIST_PATH" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>${LABEL}</string>

    <key>ProgramArguments</key>
    <array>
        <string>${PYTHON}</string>
        <string>${PROJECT_DIR}/sensors/ingestor.py</string>
    </array>

    <key>WorkingDirectory</key>
    <string>${PROJECT_DIR}</string>

    <key>EnvironmentVariables</key>
    <dict>
        <key>PYTHONPATH</key>
        <string>${PROJECT_DIR}:${PROJECT_DIR}/core</string>
        <key>INGEST_API_URL</key>
        <string>http://localhost:8000/ingest</string>
    </dict>

    <!-- Restart automatically if the process exits -->
    <key>KeepAlive</key>
    <true/>

    <!-- Start on login -->
    <key>RunAtLoad</key>
    <true/>

    <key>StandardOutPath</key>
    <string>${LOG_DIR}/engram_ingestor.out.log</string>

    <key>StandardErrorPath</key>
    <string>${LOG_DIR}/engram_ingestor.err.log</string>

    <!-- Throttle restarts — wait 10 s before restarting after a crash -->
    <key>ThrottleInterval</key>
    <integer>10</integer>
</dict>
</plist>
PLIST

launchctl load "$PLIST_PATH"

echo ""
echo "Engram ingestor installed and started."
echo "  Status:  launchctl list $LABEL"
echo "  Logs:    tail -f $LOG_DIR/engram_ingestor.out.log"
echo "  Remove:  ./scripts/uninstall_ingestor.sh"
