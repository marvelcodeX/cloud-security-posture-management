#!/usr/bin/env bash
# Local backend test runner. Runs Phase 1 rule tests and Phase 2 API tests.
set -euo pipefail

cd "$(dirname "$0")/.."
PYTHON_BIN="${PYTHON:-}"

if [[ -z "$PYTHON_BIN" ]]; then
  if [[ -x ".venv/bin/python" ]]; then
    PYTHON_BIN=".venv/bin/python"
  elif command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN="python3"
  else
    PYTHON_BIN="python"
  fi
fi

"$PYTHON_BIN" -m pytest backend/tests -q "$@"
