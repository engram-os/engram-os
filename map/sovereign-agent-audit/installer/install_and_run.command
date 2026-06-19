#!/usr/bin/env bash
set -euo pipefail

DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"

echo "Engram Sovereign Agent Audit"
echo "Put PDFs into the input folder, then press Return."
read -r

chmod +x run_audit.sh
./run_audit.sh

open "http://localhost:8000/dashboard/"
