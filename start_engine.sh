#!/usr/bin/env bash
# ================================================================
#   Pulse AI Discovery Engine — macOS & Linux 1-Click Launcher
# ================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "================================================================"
echo "   Starting Pulse AI Discovery Engine (macOS/Linux Launcher)"
echo "================================================================"

# Find Python interpreter
PYTHON_CMD=""
if [ -d "$SCRIPT_DIR/backend/.venv/bin" ]; then
    PYTHON_CMD="$SCRIPT_DIR/backend/.venv/bin/python"
elif [ -d "$SCRIPT_DIR/.venv/bin" ]; then
    PYTHON_CMD="$SCRIPT_DIR/.venv/bin/python"
elif command -v python3 &>/dev/null; then
    PYTHON_CMD="python3"
elif command -v python &>/dev/null; then
    PYTHON_CMD="python"
else
    echo "Error: Python 3 is not installed or not in PATH."
    echo "Please install Python 3.9+ from https://python.org or via package manager."
    exit 1
fi

echo "Using Python: $($PYTHON_CMD --version) at $PYTHON_CMD"

# Launch self-bootstrapping engine supervisor
$PYTHON_CMD run_engine_24x7.py
