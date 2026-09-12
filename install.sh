#!/usr/bin/env bash
# POSIX Bash Installer for it-agent-team plugin
# Strictly English only. No icons or emojis.

set -euo pipefail

REPO_URL="https://github.com/Kaivian/it-agent-team.git"
TARGET_DIR="${HOME}/.gemini/config/plugins/agent-team"
CONFIG_FILE="${HOME}/.gemini/config/config.json"

echo "=================================================="
echo "IT Agent Team Plugin: Unix/macOS Installer"
echo "Target Directory: ${TARGET_DIR}"
echo "=================================================="

# --------------------------------------------------
# Step 1: Prerequisite Verification
# --------------------------------------------------
echo "[1/4] Verifying system prerequisites..."

# 1a. Check Git CLI
if ! command -v git >/dev/null 2>&1; then
    echo "[FAIL] Git CLI is not installed or not in system PATH. Please install Git and rerun." >&2
    exit 1
fi
GIT_VER="$(git --version 2>/dev/null | tr -d '\r\n')"
echo "  [PASS] Git: ${GIT_VER}"

# 1b. Check Python 3 (>= 3.10)
PYTHON_BIN=""
if command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN="python3"
elif command -v python >/dev/null 2>&1; then
    PYTHON_BIN="python"
fi

if [ -z "${PYTHON_BIN}" ]; then
    echo "[FAIL] Python 3 is not installed or not in system PATH. Please install Python 3.10+ and rerun." >&2
    exit 1
fi

PY_CHECK_SCRIPT="import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}'); sys.exit(0 if sys.version_info >= (3, 10) else 1)"
PY_VERSION_OUTPUT="$("${PYTHON_BIN}" -c "${PY_CHECK_SCRIPT}" 2>&1 || true)"
if [ $? -ne 0 ]; then
    echo "[FAIL] Python version (${PY_VERSION_OUTPUT}) is below minimum required version 3.10. Please upgrade Python." >&2
    exit 1
fi
echo "  [PASS] Python: ${PY_VERSION_OUTPUT} (>= 3.10)"

# --------------------------------------------------
# Step 2: Repository Deployment
# --------------------------------------------------
echo "[2/4] Deploying repository..."
CURRENT_DIR="$(pwd -P 2>/dev/null || pwd)"

IS_SAME_DIR=0
if [ -d "${TARGET_DIR}" ]; then
    TARGET_CANON="$(cd "${TARGET_DIR}" 2>/dev/null && pwd -P || echo "${TARGET_DIR}")"
    if [ "${CURRENT_DIR}" = "${TARGET_CANON}" ]; then
        IS_SAME_DIR=1
    fi
fi

if [ -d "${TARGET_DIR}/.git" ]; then
    echo "  Updating existing Git repository at ${TARGET_DIR}..."
    if git -C "${TARGET_DIR}" pull --ff-only; then
        echo "  [PASS] Repository updated successfully."
    else
        echo "  [WARN] Git pull failed. Retaining local files." >&2
    fi
elif [ "${IS_SAME_DIR}" -eq 1 ]; then
    echo "  Installer running from within target directory (${TARGET_DIR}). Skipping clone."
    echo "  [PASS] Using local working tree."
elif [ -d "${TARGET_DIR}" ]; then
    echo "  Directory already exists at ${TARGET_DIR} without .git tracking."
    echo "  [PASS] Preserving existing directory files."
else
    echo "  Cloning repository into ${TARGET_DIR}..."
    mkdir -p "$(dirname "${TARGET_DIR}")"
    git clone "${REPO_URL}" "${TARGET_DIR}"
    echo "  [PASS] Repository cloned successfully."
fi

# --------------------------------------------------
# Step 3: Configure ~/.gemini/config/config.json
# --------------------------------------------------
echo "[3/4] Configuring Gemini plugin registry..."
mkdir -p "$(dirname "${CONFIG_FILE}")"

"${PYTHON_BIN}" -c '
import json
import sys
from pathlib import Path

config_path = Path(sys.argv[1])
if config_path.exists():
    try:
        data = json.loads(config_path.read_text(encoding="utf-8"))
    except Exception:
        data = {}
else:
    data = {}

if not isinstance(data, dict):
    data = {}

if "plugins" not in data or not isinstance(data["plugins"], dict):
    data["plugins"] = {}

if "agent-team" not in data["plugins"] or not isinstance(data["plugins"]["agent-team"], dict):
    data["plugins"]["agent-team"] = {}

data["plugins"]["agent-team"]["enabled"] = True

config_path.parent.mkdir(parents=True, exist_ok=True)
config_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
' "${CONFIG_FILE}"

echo "  [PASS] Enabled agent-team plugin in ${CONFIG_FILE}"

# --------------------------------------------------
# Step 4: Run Doctor Diagnostics
# --------------------------------------------------
echo "[4/4] Running system and plugin diagnostics..."
DOCTOR_PATH="${TARGET_DIR}/scripts/doctor.py"
if [ ! -f "${DOCTOR_PATH}" ]; then
    DOCTOR_PATH="${CURRENT_DIR}/scripts/doctor.py"
fi

if [ -f "${DOCTOR_PATH}" ]; then
    if "${PYTHON_BIN}" "${DOCTOR_PATH}"; then
        echo "  [PASS] Diagnostics completed successfully."
    else
        echo "  [WARN] Diagnostics completed with one or more warnings." >&2
    fi
else
    echo "  [WARN] Diagnostic script not found at ${DOCTOR_PATH}." >&2
fi

# --------------------------------------------------
# Installation Summary and Next Steps
# --------------------------------------------------
echo ""
echo "=================================================="
echo "Installation Complete: IT Agent Team Plugin"
echo "=================================================="
echo "Plugin Path: ${TARGET_DIR}"
echo "Config Path: ${CONFIG_FILE} (plugins.agent-team.enabled = true)"
echo ""
echo "Next Steps & Usage:"
echo "1. Antigravity & Gemini CLI:"
echo "   Run: /agent-team \"Your task description here\""
echo ""
echo "2. Claude Code Marketplace Catalog:"
echo "   Path: ${TARGET_DIR}/.claude-plugins/marketplace.json"
echo ""
echo "3. Diagnostics Utility:"
echo "   Run: python3 ${TARGET_DIR}/scripts/doctor.py"
echo "=================================================="
