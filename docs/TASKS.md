# Tareas

> Fuente oficial del estado de trabajo por fase.
> Ver [ROADMAP.md](ROADMAP.md) para la visión completa de las 20 fases.

---

## Fase 1 — Arquitectura Completa ✅ COMPLETADA

### Documentación arquitectónica creada

| Documento | Estado |
|---|---|
| `docs/ARCHITECTURE.md` v2.0 — sistema completo | ✅ |
| `docs/FIRESTORE.md` — esquema completo 30+ colecciones | ✅ |
| `docs/RBAC.md` — roles, permisos, matriz completa | ✅ |
| `docs/FOLDER_STRUCTURE.md` — estructura monorepo completa | ✅ |
| `docs/OFFLINE.md` — estrategia offline-first + sync | ✅ |
| `docs/SUBSCRIPTIONS.md` — planes SaaS + enforcement | ✅ |
| `docs/SECURITY.md` — actualización con flujo completo | ✅ |
| `docs/API.md` — endpoints completos por fase | ✅ |
| `docs/ROADMAP.md` — 20 fases definidas | ✅ |
| `docs/HANDOFF.md` — estado actualizado | ✅ |
| `README.md` — actualizado con nueva arquitectura | ✅ |

---

## Fase 2 — Modelo Firestore ✅ COMPLETADA

### Firebase Config

| Tarea | Estado |
|---|---|
| `firebase.json` — routing Hosting + emuladores | ✅ |
| `.firebaserc` — proyecto `taller-85514` | ✅ |
| `infra/firebase/firestore.rules` — Security Rules completas (16 colecciones) | ✅ |
| `infra/firebase/firestore.indexes.json` — 40 índices compuestos | ✅ |
| `infra/firebase/storage.rules` — Storage Rules por path y tipo MIME | ✅ |

### Datos semilla

| Tarea | Estado |
|---|---|
| `scripts/seed_plans.py` — 4 planes SaaS (Basic/Professional/Premium/Enterprise) | ✅ |
| `scripts/seed_permissions.py` — 45 permisos en 12 módulos | ✅ |
| `scripts/seed_roles.py` — 7 roles del sistema con permisos por defecto | ✅ |
| `scripts/seed_template.py` — plantilla base 15 secciones, 152 puntos | ✅ |

### Testing de Rules

| Tarea | Estado |
|---|---|
| `tests/firestore/rules.spec.js` — 20 tests de Security Rules | ✅ |
| `tests/firestore/package.json` — dependencias Jest + @firebase/rules-unit-testing | ✅ |
| `tests/firestore/jest.setup.js` / `jest.teardown.js` | ✅ |

---

## Fase 3 — Backend FastAPI ✅ COMPLETADA

### API Core

| Tarea | Estado |
|---|---|
| `pyproject.toml` — migrado de `python-jose` a `PyJWT>=2.8.0` + `cryptography>=42` | ✅ |
| `core/security.py` — JWT encode/decode para access + refresh tokens | ✅ |
| `core/firebase.py` — Firebase Admin SDK singleton (Firestore + Auth) | ✅ |
| `core/config.py` — todas las variables de entorno tipadas | ✅ |
| `.env.example` — actualizado con HMAC_SECRET_KEY y rate limit vars | ✅ |

### Middlewares

| Tarea | Estado |
|---|---|
| `middleware/security_headers.py` — X-Frame-Options, CSP, HSTS, etc. | ✅ |
| `middleware/rate_limit.py` — ventana deslizante por IP, límite estricto en auth | ✅ |
| `middleware/audit.py` — log de mutaciones autenticadas en Firestore | ✅ |
| Integración en `main.py` con orden correcto (CORS→RateLimit→SecurityHeaders→Audit) | ✅ |

### Dependencias FastAPI (RBAC + Plan)

| Tarea | Estado |
|---|---|
| `dependencies/auth.py` — `get_current_user`, `CurrentUser`, `OptionalUser` | ✅ |
| `dependencies/permissions.py` — `require_permission()`, `require_role()`, `require_plan_feature()` | ✅ |
| `schemas/auth.py` — `TokenPayload`, `TokenResponse`, `RefreshRequest` | ✅ |

### Testing

| Tarea | Estado |
|---|---|
| `tests/conftest.py` — mock global de Firebase Admin SDK | ✅ |
| `tests/test_main.py` — smoke tests health, security headers, rate limit, JWT, TokenPayload | ✅ |

---

## Fase 4 — Autenticación (Backend) ✅ COMPLETADA

### Core

| Tarea | Estado |
|---|---|
| `core/utils.py` — `hash_token()`, `run_sync()` | ✅ |
| `features/auth/domain/entities.py` — `AuthUser`, `UserRole` | ✅ |

### Repositorios

| Tarea | Estado |
|---|---|
| `UserRepository` — `find_by_uid()` con soft delete | ✅ |
| `RefreshTokenRepository` — `create`, `find_by_family`, `rotate`, `revoke_family` | ✅ |
| `RefreshTokenRecord` — dominio con `is_valid()`, `matches()` | ✅ |

### Casos de uso

| Tarea | Estado |
|---|---|
| `LoginUseCase` — verifica Firebase ID Token, genera par JWT, persiste hash en Firestore | ✅ |
| `RefreshUseCase` — rotación con detección de reuso (token family) | ✅ |
| `LogoutUseCase` — revocación de familia de tokens | ✅ |

### Endpoints

| Tarea | Estado |
|---|---|
| `POST /api/v1/auth/login` | ✅ |
| `POST /api/v1/auth/refresh` | ✅ |
| `POST /api/v1/auth/logout` (204) | ✅ |
| `GET /api/v1/auth/me` | ✅ |
| Rate limiting en auth paths (heredado de Fase 3) | ✅ |

### Testing

| Tarea | Estado |
|---|---|
| `tests/features/test_auth.py` — 18 tests con dependency overrides | ✅ |

---

## Fase 5 — Tenants y Usuarios ✅ COMPLETADA

### Core

| Tarea | Estado |
|---|---|
| `core/rbac.py` — constantes in-memory: 44 permisos, 7 roles, ROLE_PERMISSIONS, ASSIGNABLE_ROLES | ✅ |

### Feature tenants/

| Tarea | Estado |
|---|---|
| `features/tenants/domain/entities.py` — `Tenant` dataclass frozen | ✅ |
| `features/tenants/infrastructure/tenant_repository.py` — CRUD Firestore | ✅ |
| `features/tenants/application/use_cases.py` — Create, Get, Update, List | ✅ |
| `features/tenants/presentation/schemas.py` — CreateTenantRequest, UpdateTenantRequest, TenantResponse, SubscriptionResponse | ✅ |
| `features/tenants/presentation/router.py` — 5 endpoints | ✅ |
| `POST /api/v1/tenants` (superadmin) | ✅ |
| `GET /api/v1/tenants` (superadmin) | ✅ |
| `GET /api/v1/tenants/{id}` (superadmin o propio tenant) | ✅ |
| `PATCH /api/v1/tenants/{id}` (superadmin) | ✅ |
| `GET /api/v1/tenants/{id}/subscription` | ✅ |

### Feature users/

| Tarea | Estado |
|---|---|
| `features/users/domain/entities.py` — `User` dataclass frozen | ✅ |
| `features/users/infrastructure/user_crud_repository.py` — CRUD en `users/{uid}` | ✅ |
| `features/users/application/use_cases.py` — Create, Get, List, Update, Deactivate | ✅ |
| `features/users/presentation/schemas.py` — CreateUserRequest, UpdateUserRequest, UserResponse | ✅ |
| `features/users/presentation/router.py` — 5 endpoints | ✅ |
| `POST /api/v1/users` (users:create) | ✅ |
| `GET /api/v1/users` (users:read) | ✅ |
| `GET /api/v1/users/{uid}` (users:read o propio usuario) | ✅ |
| `PATCH /api/v1/users/{uid}` (users:update) | ✅ |
| `DELETE /api/v1/users/{uid}` — soft delete + disable Firebase Auth (users:delete) | ✅ |

### Feature roles/ (solo lectura)

| Tarea | Estado |
|---|---|
| `GET /api/v1/roles` — lista roles del sistema | ✅ |
| `GET /api/v1/permissions` — catálogo de permisos | ✅ |

### Testing

| Tarea | Estado |
|---|---|
| `tests/features/test_tenants.py` — 15 tests | ✅ |
| `tests/features/test_users.py` — 20 tests | ✅ |
| **Total acumulado: 68 tests, todos verdes** | ✅ |

---

## Fase 6 — Clientes y Vehículos ✅ COMPLETADA

### Feature clients/

| Tarea | Estado |
|---|---|
| `features/clients/domain/entities.py` — `Client` dataclass frozen | ✅ |
| `features/clients/infrastructure/client_repository.py` — CRUD Firestore + `increment_vehicle_count` | ✅ |
| `features/clients/application/use_cases.py` — Create, Get, List, Update, Delete | ✅ |
| `features/clients/presentation/schemas.py` — CreateClientRequest, UpdateClientRequest, ClientResponse | ✅ |
| `features/clients/presentation/router.py` — 5 endpoints | ✅ |
| `POST /api/v1/clients` (clients:create) | ✅ |
| `GET /api/v1/clients` (clients:read) + `?search=` (mín 2 chars) | ✅ |
| `GET /api/v1/clients/{id}` (clients:read) | ✅ |
| `PATCH /api/v1/clients/{id}` (clients:update) — recomputa `full_name` | ✅ |
| `DELETE /api/v1/clients/{id}` — soft delete (clients:delete) | ✅ |

### Feature vehicles/

| Tarea | Estado |
|---|---|
| `features/vehicles/domain/entities.py` — `Vehicle` dataclass frozen | ✅ |
| `features/vehicles/infrastructure/vehicle_repository.py` — CRUD Firestore + `find_by_plate` | ✅ |
| `features/vehicles/application/use_cases.py` — Create, Get, List, Update, Delete + `_normalize_plate` | ✅ |
| `features/vehicles/presentation/schemas.py` — fuel_type, transmission_type enums vía regex | ✅ |
| `features/vehicles/presentation/router.py` — 5 endpoints | ✅ |
| `POST /api/v1/vehicles` (vehicles:create) — normaliza patente | ✅ |
| `GET /api/v1/vehicles` (vehicles:read) + `?client_id=` + `?search=` | ✅ |
| `GET /api/v1/vehicles/{id}` (vehicles:read) | ✅ |
| `PATCH /api/v1/vehicles/{id}` (vehicles:update) | ✅ |
| `DELETE /api/v1/vehicles/{id}` — soft delete (vehicles:delete) | ✅ |

### Infraestructura

| Tarea | Estado |
|---|---|
| `api/v1/router.py` — incluye clients y vehicles routers | ✅ |
| `tests/conftest.py` — fixture `reset_rate_limiter` autouse (evita 429 entre tests) | ✅ |

### Testing

| Tarea | Estado |
|---|---|
| `tests/features/test_clients.py` — 15 tests | ✅ |
| `tests/features/test_vehicles.py` — 18 tests (incluye 5 tests de `_normalize_plate`) | ✅ |
| **Total acumulado: 104 tests, todos verdes** | ✅ |

---

## Fase 8 — Módulo de Inspecciones ✅ COMPLETADA

### Feature templates/

| Tarea | Estado |
|---|---|
| `features/templates/domain/entities.py` — `TemplateItem`, `TemplateCategory`, `InspectionTemplate` | ✅ |
| `features/templates/infrastructure/template_repository.py` — CRUD Firestore (sistema + tenant) | ✅ |
| `features/templates/application/use_cases.py` — Create, Get, List, Update, Delete | ✅ |
| `features/templates/presentation/schemas.py` — Request/Response con `from_entity()` | ✅ |
| `features/templates/presentation/router.py` — 5 endpoints | ✅ |
| `POST /api/v1/templates` (templates:manage) | ✅ |
| `GET /api/v1/templates` — sistema + propio tenant (inspections:read) | ✅ |
| `GET /api/v1/templates/{id}` (inspections:read) | ✅ |
| `PATCH /api/v1/templates/{id}` (templates:manage) | ✅ |
| `DELETE /api/v1/templates/{id}` — soft delete (templates:manage) | ✅ |

### Feature inspections/

| Tarea | Estado |
|---|---|
| `features/inspections/domain/entities.py` — `VehicleSnapshot`, `ClientSnapshot`, `Inspection`, `InspectionItem` | ✅ |
| `features/inspections/domain/workflow.py` — máquina de estados + `compute_score` | ✅ |
| `features/inspections/infrastructure/counter_repository.py` — número correlativo con transacción Firestore | ✅ |
| `features/inspections/infrastructure/inspection_repository.py` — CRUD Firestore con snapshots | ✅ |
| `features/inspections/infrastructure/item_repository.py` — subcol `inspections/{id}/items` + batch write + `count_statuses` | ✅ |
| `features/inspections/application/use_cases.py` — Create (con snapshots + template expansion), Get, List | ✅ |
| `features/inspections/application/workflow_use_cases.py` — Start, UpdateItem, Submit, Complete, Reopen, Cancel | ✅ |
| `features/inspections/presentation/schemas.py` — Request/Response con `from_entity()` | ✅ |
| `features/inspections/presentation/router.py` — 10 endpoints | ✅ |
| `POST /api/v1/inspections` — crea con snapshot vehículo/cliente + número correlativo | ✅ |
| `GET /api/v1/inspections` — filtros: status, vehicle_id, mechanic_id | ✅ |
| `GET /api/v1/inspections/{id}` — incluye ítems | ✅ |
| `PATCH /api/v1/inspections/{id}` — campos generales (observaciones, km, nivel combustible) | ✅ |
| `POST /api/v1/inspections/{id}/start` — draft → in_progress | ✅ |
| `PATCH /api/v1/inspections/{id}/items/{item_id}` — actualiza ítem + recalcula contadores | ✅ |
| `POST /api/v1/inspections/{id}/submit` — in_progress → review | ✅ |
| `POST /api/v1/inspections/{id}/complete` — review → completed + score automático | ✅ |
| `POST /api/v1/inspections/{id}/reopen` — review → in_progress | ✅ |
| `POST /api/v1/inspections/{id}/cancel` — any → cancelled | ✅ |

### Testing

| Tarea | Estado |
|---|---|
| `tests/features/test_templates.py` — 13 tests | ✅ |
| `tests/features/test_inspections.py` — 23 tests (incluye 7 tests dominio: workflow + score) | ✅ |
| **Total acumulado: 140 tests, todos verdes** | ✅ |

---

## Fase 9 — Generación de PDF ✅ COMPLETADA

### Decisiones de arquitectura

| Decisión | Valor |
|---|---|
| Biblioteca PDF | WeasyPrint (HTML → PDF); lazy import para no bloquear en Windows dev |
| Interfaz | `PdfGeneratorProtocol` (typing.Protocol) — desacoplada desde el inicio |
| Plantilla | Jinja2 HTML en `features/pdf/infrastructure/templates/` |
| Storage | Firebase Storage; URL con token de descarga persistente |
| Módulo | `features/pdf/` dentro del backend FastAPI (no servicio separado) |

### Tareas

| Tarea | Estado |
|---|---|
| `pyproject.toml` — agregar `jinja2` a deps principales, `weasyprint` a opcional `pdf` | ✅ |
| `features/pdf/domain/entities.py` — `TenantBranding`, `PdfJobRequest`, `PdfDocument`, `StoredReport` | ✅ |
| `features/pdf/domain/pdf_generator.py` — `PdfGeneratorProtocol` | ✅ |
| `features/pdf/infrastructure/jinja_renderer.py` — `JinjaHtmlRenderer` | ✅ |
| `features/pdf/infrastructure/weasyprint_generator.py` — `WeasyPrintPdfGenerator` | ✅ |
| `features/pdf/infrastructure/storage_uploader.py` — `FirebaseStorageUploader` | ✅ |
| `features/pdf/infrastructure/templates/inspection_report.html` — template Jinja2 | ✅ |
| `features/pdf/application/use_case.py` — `GenerateInspectionPdfUseCase` | ✅ |
| `features/pdf/presentation/schemas.py` — `GeneratePdfRequest`, `ReportResponse` | ✅ |
| `features/pdf/presentation/router.py` — `POST /api/v1/pdf/inspections/{id}` | ✅ |
| `api/v1/router.py` — incluir pdf_router | ✅ |
| `tests/features/test_pdf.py` — 15 tests con mocks | ✅ |

---

## Fase 10 — Códigos QR ✅ COMPLETADA

| Tarea | Estado |
|---|---|
| `pyproject.toml` — agregar `qrcode[pil]>=7.4.2` | ✅ |
| `core/config.py` — agregar `PUBLIC_BASE_URL`, `QR_TOKEN_EXPIRY_DAYS` | ✅ |
| `features/qr/domain/entities.py` — `PublicToken`, `QrCodeResult`, `InspectionSummary`, `QrVerification` | ✅ |
| `features/qr/infrastructure/hmac_signer.py` — `encode_token` + `decode_and_verify_token` (constant-time) | ✅ |
| `features/qr/infrastructure/qr_code_generator.py` — `QrCodeGenerator` (lazy import) | ✅ |
| `features/qr/infrastructure/public_token_repository.py` — CRUD colección `public_tokens` | ✅ |
| `features/qr/application/generate_use_case.py` — `GenerateQrUseCase` | ✅ |
| `features/qr/application/verify_use_case.py` — `VerifyQrUseCase` | ✅ |
| `features/qr/presentation/schemas.py` — `QrCodeResponse`, `QrVerificationResponse` | ✅ |
| `features/qr/presentation/router.py` — 3 endpoints | ✅ |
| `POST /api/v1/qr/inspections/{id}` — genera QR (auth: inspections:complete) | ✅ |
| `GET /api/v1/qr/verify/{token}` — verifica QR (público, sin JWT) | ✅ |
| `DELETE /api/v1/qr/tokens/{id}` — revoca token (auth: inspections:complete) | ✅ |
| `features/pdf/domain/entities.py` — campo `qr_code_b64` opcional en `PdfJobRequest` | ✅ |
| PDF template — sección QR en el header (incrustado como `<img>` base64) | ✅ |
| `tests/features/test_qr.py` — 19 tests | ✅ |
| **Total acumulado: 174 tests, todos verdes** | ✅ |

---

## Fase 11 — Presupuestos ✅ COMPLETADA

| Tarea | Estado |
|---|---|
| `features/estimates/domain/entities.py` — `EstimateItem`, `Estimate`, `VehicleSnapshot`+`ClientSnapshot` snapshots | ✅ |
| `features/estimates/domain/workflow.py` — máquina de estados 6 estados + `validate_transition` | ✅ |
| `features/estimates/infrastructure/counter_repository.py` — número correlativo `EST-{año}-{NNNNNN}` con `@fb_fs.transactional` | ✅ |
| `features/estimates/infrastructure/estimate_repository.py` — CRUD Firestore colección `estimates` + soft delete | ✅ |
| `features/estimates/infrastructure/item_repository.py` — subcol `estimates/{id}/items`, batch write, sum_subtotals, count | ✅ |
| `features/estimates/application/use_cases.py` — Create, Get (con ítems), List, Update (solo draft), Delete (solo draft) | ✅ |
| `features/estimates/application/workflow_use_cases.py` — Send, View, Respond, Convert, AddItem, RemoveItem | ✅ |
| `features/estimates/presentation/schemas.py` — Request/Response Pydantic | ✅ |
| `features/estimates/presentation/router.py` — 13 endpoints | ✅ |
| `POST /api/v1/estimates` — crea con snapshot vehículo/cliente + items en batch | ✅ |
| `GET /api/v1/estimates` — lista con filtros `status` e `inspection_id` | ✅ |
| `GET /api/v1/estimates/{id}` — incluye ítems | ✅ |
| `PATCH /api/v1/estimates/{id}` — actualiza campos (solo draft) | ✅ |
| `DELETE /api/v1/estimates/{id}` — soft delete (solo draft) | ✅ |
| `POST /api/v1/estimates/{id}/items` — agrega ítem + recalcula totales | ✅ |
| `DELETE /api/v1/estimates/{id}/items/{item_id}` — elimina ítem + recalcula totales | ✅ |
| `POST /api/v1/estimates/{id}/send` — draft → sent + crea `PublicToken` `budget_access` | ✅ |
| `POST /api/v1/estimates/{id}/convert` — accepted → converted | ✅ |
| `GET /api/v1/estimates/public/{token}` — portal público cliente (sin JWT, verifica HMAC) | ✅ |
| `POST /api/v1/estimates/public/{token}/respond` — cliente acepta/rechaza sin JWT | ✅ |
| `api/v1/router.py` — incluir estimates_router | ✅ |
| `tests/features/test_estimates.py` — 30 tests | ✅ |
| **Total acumulado: 204 tests, todos verdes** | ✅ |

---

## Fase 12 — Órdenes de Trabajo ✅ COMPLETADA

| Tarea | Estado |
|---|---|
| `features/work_orders/domain/entities.py` — `WorkOrder`, `WorkOrderEntry` | ✅ |
| `features/work_orders/domain/workflow.py` — 6 estados + `validate_transition` | ✅ |
| `features/work_orders/infrastructure/counter_repository.py` — `OT-{año}-{NNNNNN}` con `@fb_fs.transactional` | ✅ |
| `features/work_orders/infrastructure/work_order_repository.py` — CRUD colección `work_orders` + soft delete | ✅ |
| `features/work_orders/infrastructure/entry_repository.py` — subcol `work_orders/{id}/entries` | ✅ |
| `features/work_orders/application/use_cases.py` — Create, Get (con entries), List, Update | ✅ |
| `features/work_orders/application/workflow_use_cases.py` — Start, WaitParts, Resume, QualityCheck, Complete, Cancel, AddEntry | ✅ |
| `features/work_orders/presentation/schemas.py` — Request/Response Pydantic | ✅ |
| `features/work_orders/presentation/router.py` — 11 endpoints | ✅ |
| `POST /api/v1/work-orders` — crea OT desde presupuesto o inspección | ✅ |
| `GET /api/v1/work-orders` — lista con filtros status, mechanic_id, estimate_id | ✅ |
| `GET /api/v1/work-orders/{id}` — incluye bitácora completa | ✅ |
| `PATCH /api/v1/work-orders/{id}` — actualiza diagnosis, notes, mechanic | ✅ |
| `POST /api/v1/work-orders/{id}/start` — pending → in_progress | ✅ |
| `POST /api/v1/work-orders/{id}/wait-parts` — in_progress → waiting_parts | ✅ |
| `POST /api/v1/work-orders/{id}/resume` — waiting_parts → in_progress | ✅ |
| `POST /api/v1/work-orders/{id}/quality-check` — in_progress → quality_check | ✅ |
| `POST /api/v1/work-orders/{id}/complete` — quality_check → completed | ✅ |
| `POST /api/v1/work-orders/{id}/cancel` — any → cancelled | ✅ |
| `POST /api/v1/work-orders/{id}/entries` — nota libre a bitácora | ✅ |
| `api/v1/router.py` — incluir work_orders_router | ✅ |
| `tests/features/test_work_orders.py` — 29 tests | ✅ |
| **Total acumulado: 233 tests, todos verdes** | ✅ |

---

## Fase 13 — Portal del Cliente ✅ COMPLETADA

| Tarea | Estado |
|---|---|
| `apps/cliente/pubspec.yaml` — Flutter Web, riverpod, go_router, freezed, dio, intl, url_launcher | ✅ |
| `lib/main.dart` + `lib/app/router.dart` + `lib/app/theme.dart` | ✅ |
| `lib/core/config/app_config.dart` — `API_BASE_URL` via `--dart-define` | ✅ |
| `lib/core/network/api_client.dart` — Dio singleton con `_ExceptionInterceptor` | ✅ |
| `lib/core/network/api_exception.dart` — excepciones tipadas sealed | ✅ |
| `features/inspection_report/domain/entities/inspection_summary.dart` — `InspectionSummary`, `QrVerification` (freezed) | ✅ |
| `features/inspection_report/domain/repositories/inspection_report_repository.dart` — interfaz abstract | ✅ |
| `features/inspection_report/infrastructure/models/qr_verification_model.dart` — freezed+json mapper | ✅ |
| `features/inspection_report/infrastructure/datasources/inspection_api_datasource.dart` | ✅ |
| `features/inspection_report/infrastructure/repositories/inspection_report_repository_impl.dart` | ✅ |
| `features/inspection_report/application/providers/inspection_report_provider.dart` — `@riverpod` | ✅ |
| `features/inspection_report/presentation/pages/inspection_report_page.dart` | ✅ |
| `features/inspection_report/presentation/widgets/score_banner.dart` | ✅ |
| `features/inspection_report/presentation/widgets/vehicle_info_card.dart` | ✅ |
| `features/inspection_report/presentation/widgets/verification_badge.dart` | ✅ |
| `features/estimate/domain/entities/public_estimate.dart` — `PublicEstimate`, `EstimateItemEntity`, snapshots (freezed) | ✅ |
| `features/estimate/domain/repositories/estimate_repository.dart` — interfaz abstract | ✅ |
| `features/estimate/infrastructure/models/public_estimate_model.dart` — freezed+json mapper | ✅ |
| `features/estimate/infrastructure/datasources/estimate_api_datasource.dart` | ✅ |
| `features/estimate/infrastructure/repositories/estimate_repository_impl.dart` | ✅ |
| `features/estimate/application/providers/estimate_provider.dart` — `@riverpod`, `EstimateRespond` notifier | ✅ |
| `features/estimate/presentation/pages/estimate_page.dart` — vista completa con estado y respuesta | ✅ |
| `features/estimate/presentation/widgets/estimate_items_list.dart` — agrupado por categoría | ✅ |
| `features/estimate/presentation/widgets/estimate_total_section.dart` — subtotal, IVA, total | ✅ |
| `features/estimate/presentation/widgets/respond_bottom_sheet.dart` — aceptar/rechazar con nota | ✅ |
| `features/shared/presentation/pages/not_found_page.dart` | ✅ |
| `features/shared/presentation/widgets/loading_screen.dart` | ✅ |
| `features/shared/presentation/widgets/error_screen.dart` | ✅ |
| `web/index.html` + `web/manifest.json` — PWA config | ✅ |
| Rutas: `/` (landing), `/informe/:token`, `/presupuesto/:token` | ✅ |

---

---

## Infraestructura & Despliegue — Etapa 1 ✅ COMPLETADA

> Iniciada entre Fases 13 y 14. No es una fase de negocio — es la base de despliegue.

| Tarea | Estado |
|---|---|
| `.gitignore` — corregir (`.firebaserc` no debe ignorarse, agregar patrones docker/node) | ✅ |
| `.editorconfig` — estándares de formateo para Python, Dart, JSON, YAML | ✅ |
| `firebase.json` — corregir target `web-client→web-cliente`, fix paths, CSP headers, HSTS | ✅ |
| `.firebaserc` — corregir target names, agregar alias `staging` | ✅ |
| `backend/app/core/config.py` — expandir con variables de producción (GCP, Email, Twilio, PDF, Sentry) | ✅ |
| `backend/.env.example` — expandir con todas las variables documentadas | ✅ |
| `apps/cliente/.env.example` + `.dart-defines.example.json` | ✅ |
| `apps/web_admin/.env.example` | ✅ |
| `apps/mobile/.env.example` | ✅ |
| `.env.example` (root) — pointer a todos los componentes | ✅ |
| `docs/ENVIRONMENT_VARIABLES.md` — referencia completa con tabla de todas las variables | ✅ |

**Infraestructura completada** — toda la documentación y tooling de despliegue está lista.
Próximo paso: retomar **Fase 14 — Agenda** del roadmap de negocio.

---

## Fases 14-21 ⏳ PENDIENTES

> **Nota (2026-06-30):** El roadmap fue reorganizado a 21 fases.
> - Fase 7 (Portal del Cliente) movida a **Fase 13** — depende de Fases 8-12.
> - Las antiguas Fases 13-20 se renumeraron como Fases 14-21.
> - Total: 21 fases.

Cada fase se detallará con tareas granulares al comenzar.
Ver [ROADMAP.md](ROADMAP.md) para el scope completo de cada fase.

---

## Historial de Fases Completadas

| Fecha | Fase | Descripción | Commit |
|---|---|---|---|
| 2026-06-30 | Fase 0 | Foundation & Scaffolding | `feat(foundation): initial project scaffold` |
| 2026-06-30 | Fase 1 | Arquitectura completa documentada | `docs(architecture): complete v2.0 platform architecture` |
| 2026-06-30 | Fase 2 | Modelo Firestore — rules, indexes, storage, seeds | `feat(firestore): complete firestore model with security rules` |
| 2026-06-30 | Fase 3 | Backend FastAPI — core, middlewares, dependencias, tests | `feat(backend): add jwt security, middlewares and rbac dependencies` |
| 2026-06-30 | Fase 4 | Autenticación backend — login, refresh, logout, me | `feat(auth): add firebase login flow with jwt rotation and token family` |
| 2026-06-30 | Fase 5 | Tenants, usuarios y RBAC endpoints | `feat(tenants,users): add tenant and user management with rbac` |
| 2026-06-30 | Fase 6 | Clientes y vehículos — CRUD completo, búsqueda, normalización de patente | `feat(clients,vehicles): add client and vehicle management` |
| 2026-06-30 | Fase 8 | Inspecciones — workflow completo, templates, items, snapshots | `feat(inspections): add complete inspection workflow with templates` |
| 2026-06-30 | Fase 9 | PDF — generación HTML→PDF con Jinja2+WeasyPrint, Firebase Storage | `feat(pdf): add inspection pdf generation with firebase storage` |
| 2026-06-30 | Fase 10 | QR — tokens HMAC-SHA256, portal público, revocación | `feat(qr): add signed qr codes with public verification portal` |
| 2026-06-30 | Fase 11 | Presupuestos — CRUD, workflow, ítems, portal cliente HMAC | `feat(estimates): add estimate workflow with public client portal` |
| 2026-06-30 | Fase 12 | Órdenes de Trabajo — CRUD, workflow 6 estados, bitácora | `feat(work-orders): add work order workflow with status history` |
| 2026-06-30 | Fase 13 | Portal del Cliente — Flutter Web, QR + presupuestos públicos | `feat(cliente): add public client portal` |
| 2026-06-30 | Infra E1 | Variables de entorno, config base, firebase.json, .editorconfig | `chore(infra): add environment configuration and base project files` |
| 2026-06-30 | Infra E2 | Dockerfile, docker-compose, Makefile, scripts/, SETUP.md, LOCAL_DEVELOPMENT.md | `chore(infra): add docker, makefile and local development tooling` |
| 2026-06-30 | Infra E3 | GitHub Actions CI/CD (ci.yml, deploy-backend.yml, deploy-hosting.yml), CI_CD.md | `chore(ci): add github actions workflows for ci and cloud run deploy` |
| 2026-06-30 | Infra E4 | GOOGLE_CLOUD.md, FIREBASE.md, DEPLOYMENT.md, DOMAIN_CONFIGURATION.md | `docs(infra): add complete cloud, firebase, deployment and domain guides` |
| 2026-06-30 | Infra E5 | MONITORING.md, SECURITY_CHECKLIST.md, BACKUPS.md, scripts/backup_firestore.sh | `docs(infra): add monitoring, security checklist and backup strategy` |
