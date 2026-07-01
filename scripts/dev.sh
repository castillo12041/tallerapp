#!/usr/bin/env bash
# ============================================================
# dev.sh — Inicia el backend FastAPI con hot reload
#
# Uso: bash scripts/dev.sh
#      make dev
# ============================================================
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"

cd "$BACKEND_DIR"

if [[ ! -f ".env" ]]; then
  echo "ERROR: Falta backend/.env"
  echo "Ejecutar: make setup"
  exit 1
fi

if [[ ! -f "firebase_credentials.json" ]]; then
  echo "ADVERTENCIA: Falta backend/firebase_credentials.json"
  echo "El backend iniciará pero no podrá conectarse a Firebase."
fi

if [[ ! -d ".venv" ]]; then
  echo "ERROR: Entorno virtual no encontrado."
  echo "Ejecutar: make setup"
  exit 1
fi

# shellcheck disable=SC1091
source .venv/bin/activate

echo ""
echo "  → Backend iniciando..."
echo "  → URL: http://localhost:8000"
echo "  → Docs: http://localhost:8000/api/v1/openapi.json"
echo "  → Ctrl+C para detener"
echo ""

uvicorn app.main:app \
  --host 0.0.0.0 \
  --port 8000 \
  --reload \
  --reload-dir app \
  --log-level debug
