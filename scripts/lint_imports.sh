#!/bin/bash
# lint_imports.sh — Fail if any .py file outside the allowlist bypasses the NetworkGateway.
# Checks both raw `import requests` and direct `from ollama import Client` usage.
# Run as a pre-commit check or in CI: bash scripts/lint_imports.sh

set -euo pipefail

FAIL=0

# ── Check 1: raw requests import ─────────────────────────────────────────────
REQUESTS_VIOLATIONS=$(grep -r "import requests" --include="*.py" \
  --exclude-dir=venv \
  --exclude-dir=auth_venv \
  --exclude-dir=.git \
  . \
  | grep -v "^./core/network_gateway.py:" \
  | grep -v "^./scripts/" \
  | grep -v "^./tests/" \
  || true)

if [ -n "$REQUESTS_VIOLATIONS" ]; then
  echo "❌ Direct 'import requests' found outside core/network_gateway.py:"
  echo "$REQUESTS_VIOLATIONS"
  echo "   Use 'from core.network_gateway import gateway' instead."
  echo ""
  FAIL=1
fi

# ── Check 2: ollama SDK Client used directly (bypasses gateway logging) ───────
OLLAMA_VIOLATIONS=$(grep -r "from ollama import Client" --include="*.py" \
  --exclude-dir=venv \
  --exclude-dir=auth_venv \
  --exclude-dir=.git \
  . \
  | grep -v "^./scripts/" \
  | grep -v "^./tests/" \
  || true)

if [ -n "$OLLAMA_VIOLATIONS" ]; then
  echo "❌ Direct 'from ollama import Client' found — bypasses NetworkGateway logging:"
  echo "$OLLAMA_VIOLATIONS"
  echo "   Use 'gateway.post(\"ollama\", \"/api/chat\", ...)' instead."
  echo ""
  FAIL=1
fi

if [ "$FAIL" -eq 1 ]; then
  exit 1
fi

echo "✓ No gateway bypass violations found."
exit 0
