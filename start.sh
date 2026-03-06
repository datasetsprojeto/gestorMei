#!/bin/bash
set -e

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
PYTHON_BIN="python"

if [ -x "$ROOT_DIR/.venv/bin/python" ]; then
  PYTHON_BIN="$ROOT_DIR/.venv/bin/python"
fi

echo "Iniciando GestorMEI..."
echo "[1/2] Subindo backend na porta 5000..."
(
  cd "$ROOT_DIR/backend"
  "$PYTHON_BIN" run.py
) &

sleep 4

echo "[2/2] Subindo frontend na porta 5501..."
(
  cd "$ROOT_DIR/frontend"
  "$PYTHON_BIN" -m http.server 5501
) &

echo "Pronto. Backend: http://localhost:5000 | Frontend: http://localhost:5501/index.html"
wait
