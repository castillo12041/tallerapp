# ============================================================
# Taller Inspección — Backend FastAPI
# Multi-stage build: builder → runtime
#
# Build producción:
#   docker build -t tallerapp-backend .
#
# Build con tag de versión:
#   docker build -t tallerapp-backend:1.0.0 .
# ============================================================

# ---- Stage 1: Builder ----------------------------------------
FROM python:3.12-slim AS builder

WORKDIR /build

# Instalar dependencias del sistema necesarias para compilar paquetes Python
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Copiar archivos de dependencias primero (mejor cache de capas)
COPY requirements.prod.txt .

# Instalar paquetes en directorio local del usuario (aislado)
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir --user -r requirements.prod.txt


# ---- Stage 2: Runtime ----------------------------------------
FROM python:3.12-slim AS runtime

# Sistema operativo: librerías necesarias para WeasyPrint en runtime
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libharfbuzz0b \
    libfontconfig1 \
    libcairo2 \
    libgdk-pixbuf-2.0-0 \
    shared-mime-info \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Usuario no-root por seguridad
RUN groupadd -r appuser && useradd -r -g appuser appuser

WORKDIR /app

# Copiar paquetes Python instalados desde el builder
COPY --from=builder --chown=appuser:appuser /root/.local /home/appuser/.local

# Copiar código fuente de la aplicación
COPY --chown=appuser:appuser . .

# Cambiar a usuario no-root
USER appuser

# Variables de entorno para Python
ENV PATH=/home/appuser/.local/bin:$PATH
ENV PYTHONPATH=/app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

# Producción: 2 workers por defecto.
# Cloud Run overridea con --workers según CPU disponible.
CMD ["uvicorn", "app.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "2", \
     "--access-log"]
