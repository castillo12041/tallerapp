#!/usr/bin/env bash
# ============================================================
# test.sh — Ejecuta los tests del backend
#
# Uso: bash scripts/test.sh [--cov] [--fast] [PATTERN]
#      make test
#      make test-cov
#
# Opciones:
#   --cov     Generar reporte HTML de cobertura
#   --fast    Solo ejecutar tests marcados con @pytest.mark.fast
#   PATTERN   Filtrar tests por nombre (ej: test_auth)
# ============================================================
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"

cd "$BACKEND_DIR"

if [[ ! -d ".venv" ]]; then
  echo "ERROR: Entorno virtual no encontrado. Ejecutar: make setup"
  exit 1
fi

# shellcheck disable=SC1091
source .venv/bin/activate

# Parsear argumentos
COVERAGE=false
FAST=false
PATTERN=""

for arg in "$@"; do
  case $arg in
    --cov)     COVERAGE=true ;;
    --fast)    FAST=true ;;
    *)         PATTERN="$arg" ;;
  esac
done

# Construir comando pytest
PYTEST_ARGS=("-v" "--tb=short")

if [[ "$FAST" == "true" ]]; then
  PYTEST_ARGS+=("-m" "fast")
fi

if [[ "$COVERAGE" == "true" ]]; then
  PYTEST_ARGS+=(
    "--cov=app"
    "--cov-report=html"
    "--cov-report=term-missing"
    "--cov-fail-under=80"
  )
fi

if [[ -n "$PATTERN" ]]; then
  PYTEST_ARGS+=("-k" "$PATTERN")
fi

echo ""
echo "  → Ejecutando tests..."
echo ""

pytest tests/ "${PYTEST_ARGS[@]}"
EXIT_CODE=$?

if [[ "$COVERAGE" == "true" ]] && [[ $EXIT_CODE -eq 0 ]]; then
  echo ""
  echo "  → Reporte de cobertura: backend/htmlcov/index.html"
fi

exit $EXIT_CODE
