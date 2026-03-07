#!/bin/bash
# lint_imports.sh — Fail if any .py file outside the allowlist uses `import requests` directly.
# Run as a pre-commit check or in CI: bash scripts/lint_imports.sh

set -euo pipefail

VIOLATIONS=$(grep -r "import requests" --include="*.py" \
  --exclude-dir=venv \
  --exclude-dir=auth_venv \
  --exclude-dir=.git \
  . \
  | grep -v "^./core/network_gateway.py:" \
  | grep -v "^./scripts/" \
  | grep -v "^./tests/" \
  || true)

if [ -n "$VIOLATIONS" ]; then
  echo "❌ Direct 'import requests' found outside core/network_gateway.py:"
  echo "$VIOLATIONS"
  echo ""
  echo "Use 'from core.network_gateway import gateway' instead."
  exit 1
fi

echo "✓ No raw 'import requests' violations found."
exit 0
