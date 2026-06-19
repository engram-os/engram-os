#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 is required."
  exit 1
fi

if [ ! -d ".venv" ]; then
  python3 -m venv .venv
fi

if ! .venv/bin/python -c "import pypdf" >/dev/null 2>&1; then
  .venv/bin/python -m pip install -q pypdf
fi

mkdir -p input outputs/latest logs

if ! docker compose ps qdrant >/dev/null 2>&1; then
  docker compose up -d qdrant
else
  docker compose up -d qdrant
fi

.venv/bin/python audit_pipeline.py --input input --output outputs/latest

if [ -f ".dashboard.pid" ] && kill -0 "$(cat .dashboard.pid)" >/dev/null 2>&1; then
  :
else
  nohup .venv/bin/python -m http.server 8000 > logs/dashboard.log 2>&1 &
  echo $! > .dashboard.pid
fi

echo ""
echo "Dashboard: http://localhost:8000/dashboard/"
echo "Summary:   $ROOT/outputs/latest/summary.txt"
echo "Proof:     $ROOT/outputs/latest/proof.json"
