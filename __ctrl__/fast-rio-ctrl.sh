#!/usr/bin/env bash
# Main CLI entry (pair with fast-rio-ctrl.bat).
set -euo pipefail
cd "$(cd "$(dirname "$0")" && pwd)"

if [[ ! -x .venv/bin/python ]]; then
  echo "[fast-rio-ctrl] Creating .venv and installing requirements..."
  if command -v python3 >/dev/null 2>&1; then
    python3 -m venv .venv
  else
    python -m venv .venv
  fi
  .venv/bin/pip install -r requirements.txt
fi

PY=(.venv/bin/python)

if [[ $# -eq 0 ]]; then
  exec "${PY[@]}" main.py
fi
exec "${PY[@]}" main.py "$@"
