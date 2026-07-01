# HANDOFF — Estado del Proyecto

> Documento de continuidad entre sesiones de desarrollo.
> **Actualizar siempre al finalizar una sesión.**

---

## Última actualización

| Campo | Valor |
|---|---|
| Fecha | 2026-07-01 |
| Sesión | Fase 14 — Agenda + Deploy producción |
| Fase completada | Fase 14 ✅ |
| Próxima fase | Fase 15 — Dashboard y Analytics |

---

## Estado general del proyecto

| Área | Estado |
|---|---|
| Backend (FastAPI) | ✅ Fases 0–12 completas. 233 tests pasando. |
| Flutter Web Portal | ✅ Fase 13 completa. `apps/cliente/` listo. |
| Flutter App Principal | ⏳ No iniciada (Fase 14+ incluye UI mobile/web admin) |
| Infraestructura — Etapa 1 | ✅ Variables de entorno, config base, firebase.json |
| Infraestructura — Etapa 2 | ✅ Dockerfile, docker-compose, Makefile, scripts/, SETUP.md, LOCAL_DEVELOPMENT.md |
| Infraestructura — Etapa 3 | ✅ GitHub Actions: ci.yml, deploy-backend.yml, deploy-hosting.yml, CI_CD.md |
| Infraestructura — Etapa 4 | ✅ GOOGLE_CLOUD.md, FIREBASE.md, DEPLOYMENT.md, DOMAIN_CONFIGURATION.md |
| Infraestructura — Etapa 5 | ✅ MONITORING.md, SECURITY_CHECKLIST.md, BACKUPS.md, scripts/backup_firestore.sh |
| Infraestructura — Producción | ✅ GCP + Firebase + Cloud Run + Hosting + DNS configurados |
| Backend API | ✅ Fases 0–14 completas. 255 tests pasando. |
| Deploy producción | ✅ `https://api.tallerinspeccion.tapsolutions.cl` |
| Portal Cliente | ✅ `https://taller-cliente-85514.web.app` |

---

## Orden de Fases

- **Fases 0–12** ✅ Completas (backend + dominio completo)
- **Fase 13** ✅ Portal del Cliente — `apps/cliente/` Flutter Web
- **Fase 14** ✅ Agenda — `app/features/appointments/` backend completo
- **Fase 15** ⏳ **SIGUIENTE** — Dashboard y Analytics
- **Fases 16–21** ⏳ Pendientes

---

## Fases completadas en esta sesión

### Fase 11 — Presupuestos ✅

**Backend:**
- `app/features/estimates/` — domain, infrastructure, application, presentation
- 13 endpoints en `/api/v1/estimates` + `/api/v1/estimates/public/{token}`
- Workflow: `draft → sent → viewed → accepted/rejected → converted`
- Numeración correlativa: `EST-{año}-{NNNNNN}`
- `PublicToken` con HMAC-SHA256 para acceso sin login

### Fase 12 — Órdenes de Trabajo ✅

**Backend:**
- `app/features/work_orders/` — domain, infrastructure, application, presentation
- 11 endpoints en `/api/v1/work-orders`
- Workflow: `pending → in_progress → waiting_parts → quality_check → completed/cancelled`
- Subcollección `entries` (bitácora de cambios de estado)
- Numeración correlativa: `OT-{año}-{NNNNNN}`

### Fase 13 — Portal del Cliente ✅

**Flutter Web** (`apps/cliente/`):
- Portal público para clientes finales (sin Firebase Auth)
- `/informe/:token` — muestra informe de inspección vía QR token
- `/presupuesto/:token` — muestra presupuesto y permite aceptar/rechazar
- Riverpod + GoRouter + Freezed + Dio
- Tokens HMAC-SHA256 compartidos con backend

---

## Archivos clave a conocer

### Backend

```
backend/app/
├── core/
│   ├── config.py             # Settings, PUBLIC_BASE_URL, PUBLIC_TOKEN_SECRET
│   ├── auth/jwt.py           # JWT + decode_and_verify_token (HMAC-SHA256)
│   └── rbac.py               # 44 permisos, 7 roles
├── features/
│   ├── public_tokens/        # Compartido: QR + budget_access tokens
│   ├── inspections/          # Workflow + PDF + QR
│   ├── estimates/            # Presupuestos con token público
│   └── work_orders/          # OTs con bitácora
└── api/v1/router.py          # Todos los routers incluidos
```

### Flutter Web Portal

```
apps/cliente/lib/
├── main.dart                 # ProviderScope + MaterialApp.router
├── app/
│   ├── router.dart           # GoRouter: /, /informe/:token, /presupuesto/:token
│   └── theme.dart            # Material 3, seed color #1565C0
├── core/
│   ├── config/app_config.dart      # API_BASE_URL via --dart-define
│   └── network/
│       ├── api_client.dart         # Dio singleton con interceptor
│       └── api_exception.dart      # Sealed exceptions tipadas
└── features/
    ├── inspection_report/          # QrVerification, InspectionSummary
    └── estimate/                   # PublicEstimate + responder
```

---

## Pasos pendientes antes de la siguiente sesión

1. **Ejecutar `dart run build_runner build`** en `apps/cliente/` para generar
   `.freezed.dart` y `.g.dart`. Sin esto el proyecto Flutter no compila.

2. **Infraestructura — acciones manuales requeridas en GCP/Firebase:**
   - Ejecutar `docs/GOOGLE_CLOUD.md` pasos 1-10 (crear SA, secretos, AR, Cloud Run)
   - Ejecutar `docs/FIREBASE.md` (habilitar Auth, Firestore, Storage, Hosting)
   - Configurar GitHub Variables/Secrets (ver `docs/CI_CD.md`)
   - Configurar DNS (ver `docs/DOMAIN_CONFIGURATION.md`)
   - Ejecutar `make seed` para crear SuperAdmin inicial

3. **No hay pendientes de backend** — 233/233 tests pasan.

---

## Fase 14 — Agenda (próxima sesión)

### Scope

Calendario de eventos y citas para el taller.

**Dominio:**
- Entidad `Appointment` con tipos: `inspection`, `work_order`, `appointment`, `reminder`
- Estados: `scheduled`, `confirmed`, `in_progress`, `completed`, `cancelled`, `no_show`
- Vinculación opcional con cliente, vehículo, mecánico
- Recordatorios: N minutos antes del evento

**Backend (FastAPI):**
- `app/features/appointments/` — Clean Architecture + DDD
- Colección Firestore `appointments` (con `tenantId`, softDelete)
- Índices: `[tenantId, startAt]`, `[tenantId, mechanicId, startAt]`, `[tenantId, status]`
- Endpoints:
  - `POST /appointments` — crear cita
  - `GET /appointments` — listar con filtros: `?date=`, `?mechanic_id=`, `?status=`, `?type=`
  - `GET /appointments/{id}` — obtener
  - `PATCH /appointments/{id}` — actualizar (solo futuras)
  - `DELETE /appointments/{id}` — soft delete
  - `POST /appointments/{id}/confirm` — confirmar
  - `POST /appointments/{id}/cancel` — cancelar con razón
  - `GET /appointments/availability` — slots disponibles por mecánico

**Permisos RBAC** (agregar a `core/rbac.py`):
- `appointments:read`, `appointments:write`, `appointments:delete`

**Tests:**
- ≥ 80% cobertura
- Test de conflictos de horario
- Test de filtros por fecha/mecánico

---

## Decisiones técnicas importantes (no obvias)

1. **`run_sync(repo.method, arg1, arg2)`** — Firebase Admin SDK es síncrono.
   Se envuelve con `loop.run_in_executor(None, func, *args)` para uso async en FastAPI.
   Ver: `backend/app/core/firebase.py`.

2. **`@fb_fs.transactional`** — para contadores correlativos (EST-, OT-, INS-).
   Garantiza atomicidad en Firestore. Ver cualquier `counter_repository.py`.

3. **Multi-tenancy**: NUNCA queries sin filtro `tenant_id`. Toda query lleva
   `.where("tenantId", "==", tenant_id)` como primera condición.

4. **Soft delete**: nunca `document.delete()` en registros críticos.
   Usar `deleted_at` + `is_deleted: true`. Ver `DeleteEstimateUseCase`.

5. **`PublicToken.resource_id`** es genérico — `qr_inspection` guarda `inspection_id`,
   `budget_access` guarda `estimate_id`. Mismo repositorio para ambos tipos.

6. **Flutter Portal**: No usa Firebase Auth. Todo acceso es por token HMAC en URL.
   `ApiClient` Dio no lleva `Authorization` header en ningún request.

---

## Commit propuesto al cerrar esta sesión

```
feat(cliente): add public client portal (Phase 13)

- Flutter Web app at apps/cliente/ for client-facing portal
- /informe/:token shows QR-verified inspection report
- /presupuesto/:token shows estimate with accept/reject flow
- Riverpod providers, GoRouter deep links, Dio API client
- Sealed exception hierarchy for typed error handling
- Material 3 theme with StatusColors utility
- No Firebase Auth — HMAC token-based access only

Co-authored-by: Claude Sonnet 4.6
```
