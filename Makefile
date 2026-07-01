# ============================================================
# Taller Inspección — Makefile
# Punto de entrada unificado para tareas de desarrollo.
#
# Requerimientos: make (en Windows: WSL2, Git Bash o choco install make)
# ============================================================

.DEFAULT_GOAL := help
.PHONY: help setup dev dev-docker test test-cov lint lint-fix \
        build up down logs \
        build-cliente build-admin \
        deploy-hosting emulators \
        generate-cliente seed clean

BACKEND_DIR   := backend
CLIENTE_DIR   := apps/cliente
ADMIN_DIR     := apps/web_admin
MOBILE_DIR    := apps/mobile
SCRIPTS_DIR   := scripts

# ============================================================
# Ayuda
# ============================================================
help:
	@echo ""
	@echo "  Taller Inspección — Tareas disponibles"
	@echo "  ======================================="
	@echo ""
	@echo "  CONFIGURACIÓN"
	@echo "  make setup            Configura el entorno desde cero"
	@echo "  make seed             Crea usuario SuperAdmin inicial"
	@echo ""
	@echo "  DESARROLLO (nativo)"
	@echo "  make dev              Backend con hot reload (uvicorn)"
	@echo "  make emulators        Firebase Emulator Suite"
	@echo ""
	@echo "  DESARROLLO (Docker)"
	@echo "  make up               docker-compose up (backend)"
	@echo "  make down             docker-compose down"
	@echo "  make logs             Logs del contenedor API"
	@echo ""
	@echo "  CALIDAD"
	@echo "  make test             Tests del backend"
	@echo "  make test-cov         Tests con reporte de cobertura"
	@echo "  make lint             Ruff + mypy"
	@echo "  make lint-fix         Auto-fix de linting"
	@echo ""
	@echo "  FLUTTER"
	@echo "  make generate-cliente Genera código Freezed/json_serializable"
	@echo "  make build-cliente    Build Flutter Web — portal cliente"
	@echo "  make build-admin      Build Flutter Web — panel admin"
	@echo ""
	@echo "  DESPLIEGUE"
	@echo "  make build            Build imagen Docker del backend"
	@echo "  make deploy-hosting   Deploy Flutter Web a Firebase Hosting"
	@echo ""
	@echo "  make clean            Limpia artefactos de build"
	@echo ""

# ============================================================
# Configuración
# ============================================================
setup:
	@bash $(SCRIPTS_DIR)/setup.sh

seed:
	@cd $(BACKEND_DIR) && python ../$(SCRIPTS_DIR)/seed_admin.py

# ============================================================
# Desarrollo nativo
# ============================================================
dev:
	@echo "→ Iniciando backend con hot reload..."
	@cd $(BACKEND_DIR) && \
		[ -f .env ] || (echo "ERROR: Falta backend/.env — copia desde backend/.env.example" && exit 1) && \
		. .venv/bin/activate && \
		uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

emulators:
	@echo "→ Iniciando Firebase Emulator Suite..."
	@firebase emulators:start

# ============================================================
# Docker
# ============================================================
build:
	@echo "→ Construyendo imagen Docker del backend..."
	@docker build -t tallerapp-backend:latest $(BACKEND_DIR)

up:
	@docker-compose up -d
	@echo "→ Backend corriendo en http://localhost:8000"
	@echo "→ Docs API: http://localhost:8000/api/v1/openapi.json"

down:
	@docker-compose down

logs:
	@docker-compose logs -f api

# ============================================================
# Calidad
# ============================================================
test:
	@cd $(BACKEND_DIR) && \
		. .venv/bin/activate && \
		pytest tests/ -v

test-cov:
	@cd $(BACKEND_DIR) && \
		. .venv/bin/activate && \
		pytest tests/ -v --cov=app --cov-report=html --cov-report=term-missing
	@echo "→ Reporte en: backend/htmlcov/index.html"

lint:
	@cd $(BACKEND_DIR) && \
		. .venv/bin/activate && \
		ruff check . && \
		mypy app/

lint-fix:
	@cd $(BACKEND_DIR) && \
		. .venv/bin/activate && \
		ruff check --fix . && \
		ruff format .

# ============================================================
# Flutter
# ============================================================
generate-cliente:
	@echo "→ Generando código Freezed/json_serializable en apps/cliente..."
	@cd $(CLIENTE_DIR) && dart run build_runner build --delete-conflicting-outputs

build-cliente:
	@echo "→ Build Flutter Web — Portal Cliente..."
	@cd $(CLIENTE_DIR) && \
		[ -f .dart-defines.json ] || (echo "ERROR: Falta apps/cliente/.dart-defines.json" && exit 1) && \
		flutter build web \
			--dart-define-from-file=.dart-defines.json \
			--release

build-admin:
	@echo "→ Build Flutter Web — Panel Admin..."
	@cd $(ADMIN_DIR) && \
		[ -f .dart-defines.json ] || (echo "ERROR: Falta apps/web_admin/.dart-defines.json" && exit 1) && \
		flutter build web \
			--dart-define-from-file=.dart-defines.json \
			--release

# ============================================================
# Despliegue
# ============================================================
deploy-hosting: build-cliente build-admin
	@echo "→ Desplegando a Firebase Hosting..."
	@firebase deploy --only hosting

# ============================================================
# Utilidades
# ============================================================
clean:
	@echo "→ Limpiando artefactos de build..."
	@rm -rf $(BACKEND_DIR)/htmlcov
	@rm -rf $(BACKEND_DIR)/.coverage
	@rm -rf $(BACKEND_DIR)/.pytest_cache
	@rm -rf $(BACKEND_DIR)/.mypy_cache
	@rm -rf $(BACKEND_DIR)/.ruff_cache
	@find $(BACKEND_DIR) -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@rm -rf $(CLIENTE_DIR)/build
	@rm -rf $(ADMIN_DIR)/build
	@echo "✓ Limpieza completa"
