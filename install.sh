#!/usr/bin/env bash
# Accepts scripts/install_plugin.py flags, including --host codex|gemini.
set -euo pipefail
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
if command -v python3 >/dev/null 2>&1; then
  PYTHON_BIN=python3
elif command -v python >/dev/null 2>&1; then
  PYTHON_BIN=python
else
  echo '[FAIL] Python 3.10 or newer is required.' >&2
  exit 1
fi
exec "${PYTHON_BIN}" "${SCRIPT_DIR}/scripts/install_plugin.py" "$@"