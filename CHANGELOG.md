# Changelog

Formato: [Conventional Commits](https://www.conventionalcommits.org/)

---

## [Unreleased] — Fase 10

### feat(qr): add HMAC-signed QR codes with public verification endpoint

- `PublicToken` entity en colección Firestore `public_tokens` (reutilizable en Fase 11 para presupuestos)
- `HmacSigner`: payload `{iid, tid, jti, iat, exp, sig}` con firma HMAC-SHA256; `hmac.compare_digest` para constant-time comparison
- `QrCodeGenerator`: PNG base64 vía `qrcode[pil]` con lazy import
- `PublicTokenRepository`: CRUD Firestore (`create`, `find_by_id`, `revoke`, `list_by_inspection`)
- `GenerateQrUseCase`: valida estado review|completed, firma token, genera PNG, persiste en Firestore
- `VerifyQrUseCase`: decodifica, verifica firma, consulta Firestore, retorna resumen de inspección
- Endpoints: `POST /api/v1/qr/inspections/{id}` (auth), `DELETE /api/v1/qr/tokens/{id}` (auth), `GET /api/v1/qr/verify/{token}` (público, sin JWT)
- PDF template actualizado: el QR se incrusta como PNG base64 (`<img>` en el header)
- `PdfJobRequest.qr_code_b64` campo opcional; flujo: generar QR → pasar b64 al PDF
- `settings.PUBLIC_BASE_URL` y `settings.QR_TOKEN_EXPIRY_DAYS` (365d por defecto)
- 19 tests (endpoints, HMAC round-trip, tamper detection, revocación, dominio)

---

## [Unreleased] — Fase 9

### feat(pdf): add inspection PDF generation with decoupled interface

- `PdfGeneratorProtocol` (typing.Protocol) — interfaz desacoplada lista para extraer a `pdf_service/` en Fase 19
- `WeasyPrintPdfGenerator`: implementación concreta con lazy import (no falla en Windows sin GTK)
- `JinjaHtmlRenderer`: template HTML responsive A4 con branding dinámico (nombre, colores, logo, pie de página)
- `FirebaseStorageUploader`: sube a Firebase Storage con token de descarga persistente (sin expiración, sin `make_public`)
- `GenerateInspectionPdfUseCase`: valida estado (`review`|`completed`), genera PDF, sube, actualiza `report_url` en la inspección
- Template incluye: encabezado con branding, datos de vehículo/cliente, checklist por categoría con badges de color, score, observaciones, firma, costo total de reparaciones
- Endpoint: `POST /api/v1/pdf/inspections/{id}` — requiere permiso `inspections:complete`
- Roadmap reorganizado: 20 → 21 fases; Portal del Cliente movido a Fase 13 (dependencias: Fases 8-12)
- 15 tests (endpoint, dominio, Jinja2, validaciones, cross-tenant)

---

## [Unreleased] — Fase 8

### feat(templates): add inspection template management

- `InspectionTemplate` entity con `TemplateCategory` y `TemplateItem` anidados (frozen dataclasses)
- `TemplateRepository.list_for_tenant()`: retorna plantillas de sistema (tenantId=None) + propias del tenant
- 5 endpoints: `POST/GET/PATCH/DELETE /api/v1/templates`
- Permisos: `templates:manage` para mutaciones; `inspections:read` para lectura (accesible a inspectores)
- `is_system` property en la entidad para diferenciar plantillas del sistema vs. tenant
- 13 tests

### feat(inspections): add full inspection module with workflow and scoring

- `Inspection` entity con `VehicleSnapshot` + `ClientSnapshot` inmutables al crear
- `InspectionItem` en subcol `inspections/{id}/items` — subcollection Firestore
- Workflow de estados: `draft → in_progress → review → completed` con `validate_transition()`
- Score automático al completar: `(good*100 + regular*50) / (evaluated*100) * 100`
- `InspectionCounterRepository` con `@fb_fs.transactional` para número correlativo `INS-{año}-{NNNNNN}`
- `ItemRepository.create_batch()` con Firestore batch write para expandir plantilla en ítems
- `ItemRepository.count_statuses()` recomputa agregados del padre tras cada actualización de ítem
- 10 endpoints: CRUD + `/start` + `/items/{id}` + `/submit` + `/complete` + `/reopen` + `/cancel`
- `CreateInspectionUseCase` inyecta VehicleRepo, ClientRepo, TemplateRepo, CounterRepo
- 23 tests (incluye 7 tests de dominio: workflow + score)

---

## [0.6.0] — 2026-06-30 — Fase 6

### feat(clients): add client management with full-text search

- `Client` frozen dataclass con `full_name` denormalizado
- `ClientRepository`: CRUD Firestore + `increment_vehicle_count` atómico
- Casos de uso: `Create`, `Get`, `List`, `Update`, `Delete`
- Endpoints: `POST/GET/PATCH/DELETE /api/v1/clients`
- Búsqueda por `?search=` (mín 2 chars) en nombre, email, RUT, teléfono
- `full_name` se recomputa al cambiar `first_name` o `last_name`
- 15 tests

### feat(vehicles): add vehicle management with plate normalization

- `Vehicle` frozen dataclass (plate ya normalizado al persistir)
- `VehicleRepository`: CRUD Firestore + `find_by_plate` para unicidad por tenant
- `_normalize_plate(plate)`: uppercase + strip guiones + strip espacios
- Casos de uso: `Create`, `Get`, `List`, `Update`, `Delete`
- Endpoints: `POST/GET/PATCH/DELETE /api/v1/vehicles`
- Filtros: `?client_id=` y `?search=` (patente, marca, modelo, VIN)
- Campos opcionales tipados: `fuel_type`, `transmission_type` (regex enum)
- 18 tests (incluye 5 unit tests de `_normalize_plate`)

### fix(tests): reset rate limiter between tests to prevent 429 bleed

- Fixture `reset_rate_limiter` en `conftest.py` (autouse, function scope)
- Traversa el middleware stack para limpiar `_requests` del `RateLimitMiddleware`
- Resuelve fallos de 9 tests al superar el límite de 60 req/min entre todos los tests

---

## [0.6.0] — 2026-06-30 — Fase 5: Tenants y Usuarios

### feat(tenants): add tenant management endpoints

- `Tenant` frozen dataclass con `is_operational` y `is_deleted`
- `TenantRepository`: CRUD Firestore con soft delete
- Casos de uso: `Create`, `Get`, `Update`, `List`
- Endpoints: `POST/GET/PATCH /api/v1/tenants`, `GET /api/v1/tenants/{id}/subscription`
- Acceso: superadmin para gestión global; tenantadmin para lectura de su propio tenant
- 15 tests

### feat(users): add user management with firebase auth sync

- `User` frozen dataclass (perfil completo con RBAC)
- `UserCrudRepository`: CRUD en `users/{uid}` global (no subcol)
- `CreateUserUseCase`: crea en Firebase Auth + Firestore + claims; rollback si Firestore falla
- `DeactivateUserUseCase`: soft delete + `firebase_auth.update_user(disabled=True)`
- Endpoints: `POST/GET/PATCH/DELETE /api/v1/users`
- `functools.partial` para kwargs en `run_sync()`
- 20 tests

### feat(rbac): add in-memory roles and permissions catalog

- `core/rbac.py`: 44 permisos en 18 módulos, 7 roles, `ROLE_PERMISSIONS`, `ASSIGNABLE_ROLES`
- `GET /api/v1/roles` — catálogo de roles del sistema
- `GET /api/v1/permissions` — catálogo completo de permisos

---

## [0.5.0] — 2026-06-30 — Fase 4: Autenticación

### feat(auth): add firebase login flow with jwt rotation and token family

- `LoginUseCase`: Firebase ID Token → par JWT interno con claims
- `RefreshUseCase`: rotación con detección de reuso (token family pattern)
- `LogoutUseCase`: revoca familia de refresh tokens
- `RefreshTokenRepository`: `rotate()` + `revoke_family()`
- Endpoints: `POST /auth/login`, `POST /auth/refresh`, `POST /auth/logout`, `GET /auth/me`
- `hash_token()` + `run_sync()` en `core/utils.py`
- 18 tests

---

## [0.4.0] — 2026-06-30 — Fase 3: Backend FastAPI

### feat(backend): add jwt security, middlewares and rbac dependencies

- `core/security.py`: JWT access (30min) + refresh (30 días) con PyJWT HS256
- `middleware/rate_limit.py`: ventana deslizante por IP (60 req/min; 10 en auth)
- `middleware/security_headers.py`: X-Frame-Options, CSP, HSTS, etc.
- `middleware/audit.py`: log de mutaciones en Firestore
- `dependencies/auth.py`: `get_current_user`, `CurrentUser`, `OptionalUser`
- `dependencies/permissions.py`: `require_permission()`, `require_role()`, `require_plan_feature()`
- `schemas/auth.py`: `TokenPayload` con `is_superadmin`, `has_permission`, `has_tenant`
- 12 tests smoke + middleware + JWT

---

## [0.3.0] — 2026-06-30 — Fase 2: Modelo Firestore

### feat(firestore): complete firestore model with security rules

- `firestore.rules`: Security Rules para 16 colecciones
- `firestore.indexes.json`: 40 índices compuestos
- `storage.rules`: Storage Security Rules por path y tipo MIME
- Scripts semilla: planes, permisos, roles de sistema, plantilla base
- 20 tests de Security Rules con Firebase Emulator

---

## [0.2.0] — 2026-06-30 — Fase 1: Arquitectura Completa

### docs(architecture): complete v2.0 platform architecture

- `docs/ARCHITECTURE.md` v2.0
- `docs/FIRESTORE.md` — esquema completo 30+ colecciones
- `docs/RBAC.md` — roles, permisos, matriz completa
- `docs/FOLDER_STRUCTURE.md` — estructura monorepo
- `docs/OFFLINE.md` — estrategia offline-first + sync
- `docs/SUBSCRIPTIONS.md` — planes SaaS + enforcement
- `docs/SECURITY.md` — flujo de seguridad completo
- `docs/API.md` — endpoints completos por fase
- `docs/ROADMAP.md` — 20 fases definidas

---

## [0.1.0] — 2026-06-30 — Fase 0: Foundation

### feat(foundation): initial project scaffold

- Monorepo: `apps/`, `backend/`, `packages/`, `docs/`, `scripts/`, `infra/`
- Backend FastAPI con estructura feature-first
- `pyproject.toml` con dependencias base
- `.env.example` completo
