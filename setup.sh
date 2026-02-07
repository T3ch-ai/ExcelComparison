#!/usr/bin/env bash
# ============================================================================
# Setup: creates a local virtual environment and installs dependencies
# ============================================================================
# Usage:
#   chmod +x setup.sh
#   ./setup.sh
#
# After running, select the .venv interpreter in VSCode:
#   Ctrl+Shift+P -> "Python: Select Interpreter" -> .venv
# ============================================================================

set -e

VENV_DIR=".venv"

echo "-- Creating virtual environment in ${VENV_DIR}/ ..."
python3 -m venv "${VENV_DIR}"

echo "-- Activating ..."
source "${VENV_DIR}/bin/activate"

echo "-- Installing packages from requirements.txt ..."
pip install --upgrade pip
pip install -r requirements.txt

echo "-- Registering Jupyter kernel ..."
python -m ipykernel install --user --name=network-adequacy --display-name "Network Adequacy (venv)"

echo ""
echo "============================================"
echo "  Setup complete."
echo "  venv location : ${VENV_DIR}/"
echo "  Activate      : source ${VENV_DIR}/bin/activate"
echo "  VSCode        : Select interpreter -> ${VENV_DIR}/bin/python"
echo "  Kernel        : 'Network Adequacy (venv)' in notebook picker"
echo "============================================"
