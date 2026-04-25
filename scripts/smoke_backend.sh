#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

cd "${ROOT_DIR}"

PYTHON_BIN=""

if [[ -x "${ROOT_DIR}/venv/bin/python" ]]; then
  PYTHON_BIN="${ROOT_DIR}/venv/bin/python"
  echo "[ok] Using virtualenv interpreter: ${PYTHON_BIN}"
elif command -v python >/dev/null 2>&1; then
  PYTHON_BIN="$(command -v python)"
  echo "[warn] venv/bin/python not found, using system interpreter: ${PYTHON_BIN}"
elif command -v python3 >/dev/null 2>&1; then
  PYTHON_BIN="$(command -v python3)"
  echo "[warn] venv/bin/python not found, using system interpreter: ${PYTHON_BIN}"
else
  echo "[error] Python interpreter not found. Create venv or install Python first."
  exit 1
fi

if ! "${PYTHON_BIN}" -c "import pytest" >/dev/null 2>&1; then
  echo "[error] pytest is not available for ${PYTHON_BIN}."
  echo "[hint] Activate venv and install dependencies: pip install -r requirements.txt"
  exit 1
fi

echo "[ok] Running backend startup smoke tests"
"${PYTHON_BIN}" -m pytest tests/test_startup_smoke.py -v
