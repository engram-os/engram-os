#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DIST="$ROOT/dist"
STAGE="$DIST/Engram-Sovereign-Agent-Audit"
DMG="$DIST/Engram-Sovereign-Agent-Audit.dmg"

rm -rf "$STAGE" "$DMG"
mkdir -p "$STAGE" "$DIST"

cp "$ROOT/audit_pipeline.py" "$STAGE/"
cp "$ROOT/run_audit.sh" "$STAGE/"
cp "$ROOT/docker-compose.yml" "$STAGE/"
cp "$ROOT/README.md" "$STAGE/"
cp "$ROOT/sample_contract.txt" "$STAGE/"
cp "$ROOT/installer/install_and_run.command" "$STAGE/"
cp -R "$ROOT/dashboard" "$STAGE/dashboard"
cp -R "$ROOT/input" "$STAGE/input"
cp -R "$ROOT/outputs" "$STAGE/outputs"
cp -R "$ROOT/logs" "$STAGE/logs"

chmod +x "$STAGE/run_audit.sh" "$STAGE/install_and_run.command"

hdiutil create -volname "Engram Audit" -srcfolder "$STAGE" -ov -format UDZO "$DMG"
rm -rf "$STAGE"

echo "Created $DMG"
