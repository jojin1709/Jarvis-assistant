#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

PYTHON="${PYTHON:-python3}"
VENV_DIR="backend/.venv"

echo "Creating virtual environment..."
"$PYTHON" -m venv "$VENV_DIR"
source "$VENV_DIR/bin/activate"

echo "Installing requirements..."
pip install --upgrade pip
pip install -r backend/requirements.txt
pip install pyinstaller

echo "Building backend binary..."
cd backend
pyinstaller \
  --onefile \
  --name jx-jarvis-backend \
  --distpath ../resources/backend-dist \
  --workpath /tmp/jarvis-build \
  --noconfirm \
  app/main.py

echo "Done. Binary: resources/backend-dist/jx-jarvis-backend"
