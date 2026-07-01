# Taller Inspección

**SaaS multi-tenant para talleres mecánicos** — Inspecciones precompra de vehículos, presupuestos, órdenes de trabajo y portal del cliente.

🌐 `tallerinspeccion.tapsolutions.cl`

---

## Stack

| Capa | Tecnología |
|---|---|
| App Mobile | Flutter 3.x (Android · iOS · PWA) · Offline-First |
| Web Admin | Flutter Web (`/admin` SuperAdmin · `/app` Taller) |
| Web Cliente | Flutter Web (`/cliente` · `/informe` · `/presupuesto`) |
| Estado | Riverpod 2.x |
| Navegación | GoRouter |
| Modelos | Freezed + JsonSerializable |
| Offline | Drift (SQLite) + SyncManager |
| Backend API | Python 3.12 + FastAPI |
| Background | Workers (tasks asíncronas) |
| PDF | WeasyPrint + ReportLab |
| Notificaciones | Email (SendGrid/SMTP) · Push (FCM) · WhatsApp (Twilio) |
| Base de datos | Firebase Firestore (30+ colecciones) |
| Autenticación | Firebase Auth + JWT + Refresh Tokens |
| Almacenamiento | Firebase Cloud Storage |
| Seguridad | RBAC · HMAC-SHA256 · Rate Limit · Audit Log |

---

## Estructura del Monorepo

```
tallerapp/
├── apps/
│   ├── mobile/        # Flutter mobile (Offline-First)
│   ├── web_admin/     # Flutter Web: /admin + /app
│   └── web_client/    # Flutter Web: /cliente + /informe + /presupuesto
├── backend/
│   ├── api/           # FastAPI principal
│   ├── workers/       # Tareas asíncronas
│   ├── notifications/ # Email · Push · WhatsApp
│   ├── pdf_service/   # Generación de PDF
│   └── integrations/  # Patentes · externos
├── packages/          # Dart/Flutter packages compartidos
├── docs/              # Documentación técnica (fuente oficial)
├── infra/             # Docker · Firebase · CI/CD
└── scripts/           # Scripts de setup y seed
```

---

## Documentación Técnica (Fuente Oficial)

| Documento | Descripción |
|---|---|
| [ARCHITECTURE.md](docs/ARCHITECTURE.md) | Arquitectura completa · diagramas · decisiones |
| [FIRESTORE.md](docs/FIRESTORE.md) | Modelo de datos Firestore · 30+ colecciones |
| [RBAC.md](docs/RBAC.md) | Roles · permisos · matriz de acceso |
| [FOLDER_STRUCTURE.md](docs/FOLDER_STRUCTURE.md) | Estructura completa del monorepo |
| [OFFLINE.md](docs/OFFLINE.md) | Estrategia offline-first + sync |
| [SUBSCRIPTIONS.md](docs/SUBSCRIPTIONS.md) | Planes SaaS · restricciones · enforcement |
| [SECURITY.md](docs/SECURITY.md) | Auth · JWT · tokens públicos · Firestore Rules |
| [API.md](docs/API.md) | Endpoints REST por fase |
| [DEVELOPMENT.md](docs/DEVELOPMENT.md) | Setup · convenciones · testing |
| [ROADMAP.md](docs/ROADMAP.md) | 20 fases de desarrollo |
| [TASKS.md](docs/TASKS.md) | Tareas activas por fase |
| [HANDOFF.md](docs/HANDOFF.md) | Estado del proyecto · continuidad entre sesiones |

---

## Setup Rápido

Ver [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) para instrucciones completas.

```bash
# Backend API
cd backend/api
pip install -r requirements.txt && cp .env.example .env
uvicorn app.main:app --reload

# Flutter Mobile
cd apps/mobile
flutterfire configure && flutter pub get && flutter run
```

---

## Estado del Proyecto

| Fase | Descripción | Estado |
|---|---|---|
| 0 | Foundation & Scaffolding | ✅ |
| 1 | Arquitectura Completa | ⏳ Aprobación pendiente |
| 2 | Modelo Firestore | — |
| 3 | Backend FastAPI | — |
| 4 | Autenticación | — |
| 5 | Flutter Base | — |
| 6 | Panel del Taller | — |
| 7 | Portal Cliente | — |
| 8 | Inspecciones | — |
| 9 | PDF | — |
| 10 | QR | — |
| 11-20 | Módulos comerciales · Analytics · CI/CD · Optimización | — |

**Fase en curso:** Fase 1 — Arquitectura (esperando aprobación)
