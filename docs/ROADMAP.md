# Roadmap — 21 Fases

> Fuente oficial de planificación. Ver [TASKS.md](TASKS.md) para tareas activas.
> Dominio: `tallerinspeccion.tapsolutions.cl`

## Estado actual

**Fase 15 — Dashboard y Analytics** — ⏳ SIGUIENTE
**Fase 14 — Agenda** — ✅ COMPLETADA
**Fase 13 — Portal del Cliente** — ✅ COMPLETADA
**Fase 12 — Órdenes de Trabajo** — ✅ COMPLETADA
**Fase 11 — Presupuestos** — ✅ COMPLETADA
**Fase 10 — Códigos QR** — ✅ COMPLETADA
**Fase 9 — Generación de PDF** — ✅ COMPLETADA
**Fase 8 — Módulo de Inspecciones (Backend)** — ✅ COMPLETADA
**Fase 6 — Clientes y Vehículos** — ✅ COMPLETADA
**Fase 5 — Tenants y Usuarios** — ✅ COMPLETADA
**Fase 4 — Autenticación (Backend)** — ✅ COMPLETADA
**Fase 3 — Backend FastAPI** — ✅ COMPLETADA
**Fase 2 — Modelo Firestore** — ✅ COMPLETADA
**Fase 1 — Arquitectura Completa** — ✅ COMPLETADA
**Fase 0 — Foundation & Scaffolding** — ✅ COMPLETADA

> **Nota de orden:** El Portal del Cliente (antes Fase 7) fue movido a Fase 13.
> Depende de: Inspecciones (Fase 8), PDF (Fase 9), QR (Fase 10),
> Presupuestos (Fase 11) y Órdenes de Trabajo (Fase 12).
> Se construye primero el dominio backend completo; luego el portal consume datos reales.

---

## Criterios de Completitud (todas las fases)

1. Tests pasan con cobertura ≥ 80%
2. Proyecto compila sin warnings ni errores de lint
3. Documentación actualizada: README, TASKS, ARCHITECTURE
4. HANDOFF.md actualizado con estado y próximos pasos
5. Commit propuesto con Conventional Commits
6. Sin deuda técnica intencional

---

## Fases

### Fase 1 — Arquitectura Completa ✅ COMPLETADA

**Objetivo:** Diseño aprobado de toda la plataforma. Sin código de producción.

- [x] Análisis completo de requisitos
- [x] Detección de problemas arquitectónicos
- [x] docs/ARCHITECTURE.md v2.0
- [x] docs/FIRESTORE.md — esquema completo de datos
- [x] docs/RBAC.md — roles y permisos
- [x] docs/FOLDER_STRUCTURE.md — estructura completa
- [x] docs/OFFLINE.md — estrategia offline-first
- [x] docs/SUBSCRIPTIONS.md — planes SaaS
- [x] docs/ROADMAP.md — 21 fases definidas

---

### Fase 2 — Modelo Firestore ✅ COMPLETADA

**Objetivo:** Firestore completamente configurado y documentado.

- Colecciones creadas con índices compuestos (`firestore.indexes.json`)
- Security Rules completas para todas las colecciones (`firestore.rules`)
- Storage Security Rules (`storage.rules`)
- `firebase.json` con routing de Firebase Hosting
- Emuladores configurados para testing local
- Datos semilla para desarrollo (planes, permisos, roles de sistema)
- Tests de Security Rules con Firebase Emulator

---

### Fase 3 — Backend FastAPI ✅ COMPLETADA

**Objetivo:** Backend base ejecutable con estructura completa de módulos.

- Feature-first bajo `app/features/`
- Todos los middlewares: auth, rate_limit, security_headers, audit
- `GET /api/v1/health`
- Variables de entorno completas (`.env.example`)
- Tests de smoke + middleware

---

### Fase 4 — Autenticación Completa ✅ COMPLETADA

**Objetivo:** Auth segura con RBAC, JWT, Refresh Tokens y multi-tenant.

- Firebase Admin SDK inicializado
- `POST /auth/login` — Firebase ID Token → JWT interno
- `POST /auth/refresh` — Refresh Token rotation
- `POST /auth/logout` — Revocación de tokens
- `GET /auth/me` — Perfil del usuario autenticado
- JWT con `tenant_id`, `role`, `permissions[]`, `plan` incrustados
- Tests de autenticación (cobertura ≥ 80%)

---

### Fase 5 — Tenants y Usuarios ✅ COMPLETADA

**Objetivo:** Multi-tenancy completo con RBAC en backend.

- CRUD de Tenants y Users con Firestore
- `core/rbac.py`: 44 permisos, 7 roles
- `GET /api/v1/roles` y `GET /api/v1/permissions`
- Tests

---

### Fase 6 — Clientes y Vehículos ✅ COMPLETADA

**Objetivo:** CRUD de clientes y vehículos con búsqueda y normalización.

- CRUD completo de clientes con búsqueda full-text
- CRUD completo de vehículos con normalización de patente
- Filtros: `?search=`, `?client_id=`
- Tests

---

### Fase 7 — (Omitida — contenido movido a Fase 13)

> El Portal del Cliente fue pospuesto. Ver Fase 13.

---

### Fase 8 — Módulo de Inspecciones ✅ COMPLETADA

**Objetivo:** Inspección precompra completa con workflow y puntuación automática.

- Plantillas de inspección con categorías y ítems configurables
- Workflow: `draft → in_progress → review → completed`
- Snapshots inmutables de vehículo y cliente al crear
- Puntuación automática al completar (0-100)
- Números correlativos: `INS-{año}-{NNNNNN}` con transacción Firestore
- 10 endpoints de inspección + 5 de plantillas
- Tests

---

### Fase 9 — Generación de PDF ⏳ SIGUIENTE

**Objetivo:** PDF profesional de inspección con branding del taller.

- `features/pdf/` como módulo dentro del backend FastAPI
- `PdfGeneratorProtocol` (typing.Protocol) — interfaz desacoplada lista para extraer
  a `pdf_service/` en Fase 19 sin cambios en la lógica de negocio
- Template HTML responsive con Jinja2 — secciones: encabezado, vehículo, cliente,
  checklist por categoría con estado visual, score, observaciones, pie de página legal
- Branding dinámico: nombre, colores, logo, dirección, teléfono del taller
- Implementación concreta: `WeasyPrintPdfGenerator` (HTML → PDF)
- Upload a Firebase Storage; URL de descarga con token persistente
- `report_url` guardado en el documento de la inspección (campo ya existe en entidad)
- Endpoint: `POST /api/v1/pdf/inspections/{id}`
- Solo genera PDF para inspecciones en estado `review` o `completed`
- Tests con mocks de generador y storage

---

### Fase 10 — Códigos QR ✅ COMPLETADA

**Objetivo:** QR seguro y verificable para cada informe.

- Generación con `qrcode` Python
- Payload: `{inspectionId, tenantId, timestamp, expiry, hash}`
- Firma HMAC-SHA256
- Endpoint de verificación: `GET /public/verify-qr/{token}`
- Incrustado en el PDF del informe
- Revocable desde el backend
- Colección `public_tokens` en Firestore

---

### Fase 11 — Presupuestos

**Objetivo:** Presupuestos con workflow completo.

- CRUD de presupuestos vinculados a inspecciones
- Items con precio unitario, cantidad, total
- Estados: `draft → sent → viewed → accepted/rejected → converted`
- Envío por email y WhatsApp
- Token público HMAC para acceso sin login: `/presupuesto/{token}`
- Conversión automática a Orden de Trabajo
- Numeración correlativa: `EST-{año}-{NNNNNN}`

---

### Fase 12 — Órdenes de Trabajo

**Objetivo:** OT vinculadas a presupuestos con tracking de progreso.

- CRUD de órdenes de trabajo
- Estados: `pending → in_progress → waiting_parts → quality_check → completed`
- Asignación a mecánico
- Historial de cambios de estado
- Numeración correlativa: `OT-{año}-{NNNNNN}`

---

### Fase 13 — Portal del Cliente (web_client)

**Objetivo:** Portal público y privado para el cliente final.

> **Dependencias satisfechas:** Fase 8 (Inspecciones), Fase 9 (PDF), Fase 10 (QR),
> Fase 11 (Presupuestos), Fase 12 (OT).

- `apps/web_client/` inicializado
- Rutas: `/cliente`, `/informe/{token}`, `/presupuesto/{token}`
- Autenticación simplificada del cliente
- Vista de informes de inspección (sin login via token público HMAC)
- Descarga de PDFs
- Vista y respuesta de presupuestos
- Sin acceso entre diferentes clientes (validación de token)

---

### Fase 14 — Agenda

**Objetivo:** Calendario de eventos, citas e inspecciones.

- Vista mensual/semanal/diaria (Flutter)
- Tipos: inspección, OT, cita, recordatorio
- Vinculación con clientes y vehículos
- Recordatorios por push/email
- Vista por mecánico asignado
- Drag & drop en web

---

### Fase 15 — Dashboard y Analytics

**Objetivo:** KPIs, métricas y reportes de productividad.

- Dashboard TenantAdmin: inspecciones/día, ingresos, usuarios activos
- KPIs: tiempo promedio, tasa de completitud, score promedio
- Gráficos con Flutter Charts
- Exportar a CSV/Excel (plan Professional+)
- Dashboard SuperAdmin: métricas globales
- Uso de storage y Firestore por tenant

---

### Fase 16 — Notificaciones

**Objetivo:** Email, push y WhatsApp automáticos.

- Email vía SMTP o SendGrid (configurable por tenant)
- Push vía Firebase Cloud Messaging
- WhatsApp vía Twilio (plan Premium+)
- Templates de notificación personalizables con branding del tenant
- Notificaciones automáticas: informe listo, presupuesto enviado, OT completada
- Registro en `emails/` y `whatsapp_messages/`
- Reintentos con backoff exponencial

---

### Fase 17 — Auditoría

**Objetivo:** Registro inmutable de toda acción en la plataforma.

- `AuditMiddleware` en FastAPI completado
- Colección `audit_logs` con todos los campos requeridos
- Panel de auditoría en web_admin (filtrable por usuario, entidad, fecha)
- Exportación de logs (Enterprise)
- Retención ilimitada
- Logs de seguridad: intentos fallidos, acceso denegado

---

### Fase 18 — PWA

**Objetivo:** App web instalable con modo offline básico.

- Flutter Web configurado como PWA
- Manifiesto web (`manifest.json`)
- Service Worker para cache de assets
- Instalable en Android/iOS/Desktop
- Push notifications vía FCM en web
- Ícono y splash screen

---

### Fase 19 — Testing Completo

**Objetivo:** Cobertura ≥ 80% en todos los módulos.

- Unit tests: dominio + servicios backend
- Integration tests: endpoints con Firebase Emulator
- Widget tests: Flutter mobile + web
- E2E tests: flujo crítico de inspección
- Performance tests: generación de PDF, sync offline
- Security tests: RBAC, tenant isolation, token verification
- Extracción opcional de `pdf_service/` como microservicio independiente

---

### Fase 20 — CI/CD

**Objetivo:** Pipeline automático de integración y despliegue.

- GitHub Actions: lint → tests → build → deploy
- Deploy backend: Docker + Google Cloud Run
- Deploy Flutter Web: Firebase Hosting (web_admin + web_client)
- Deploy Flutter Mobile: build APK/IPA en CI
- Firestore: deploy de rules + indexes automático
- Environments: development, staging, production
- Secrets en GitHub Secrets / Google Secret Manager

---

### Fase 21 — Optimización Final

**Objetivo:** Plataforma lista para miles de talleres simultáneos.

- Load testing (k6): inspecciones concurrentes, sync simultáneo
- Optimización de índices Firestore basada en datos reales
- Compresión y CDN para assets estáticos
- Rate limiting ajustado por métricas reales
- Security review completo (OWASP Top 10)
- Penetration testing
- Documentación de operaciones y runbooks
- Monitoreo: Cloud Monitoring + Crashlytics + Analytics
- Plan de backup y disaster recovery
