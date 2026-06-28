#!/usr/bin/env bash
# uninstall_ingestor.sh — Remove the Engram file-watcher launchd agent.

set -euo pipefail

LABEL="com.engram.ingestor"
PLIST_PATH="$HOME/Library/LaunchAgents/$LABEL.plist"

if [[ ! -f "$PLIST_PATH" ]]; then
    echo "Nothing to uninstall — $PLIST_PATH not found."
    exit 0
fi

launchctl unload "$PLIST_PATH" 2>/dev/null && echo "Agent stopped." || echo "Agent was not running."
rm -f "$PLIST_PATH"
echo "Removed $PLIST_PATH"
echo "Log files at ~/Library/Logs/engram_ingestor.*.log were left in place."
