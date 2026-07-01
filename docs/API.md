# Diseño de la API REST

> Fuente oficial del contrato de la API. Ver [ARCHITECTURE.md](ARCHITECTURE.md) para contexto general.

## Principios de diseño

- **RESTful**: recursos en plural, verbos HTTP semánticos
- **Versionada**: `/api/v1` estable, `/api/v2` para breaking changes
- **Auto-documentada**: OpenAPI generado automáticamente por FastAPI
- **Tipada**: Pydantic v2 valida requests y responses
- **Consistente**: mismo formato de error en toda la API
- **Multi-tenant**: cada request protegido valida el `tenantId` del token

---

## URLs base

| Entorno | URL base |
|---|---|
| Desarrollo | `http://localhost:8000` |
| Staging | `https://api-staging.tallerinspeccion.com` |
| Producción | `https://api.tallerinspeccion.com` |

## Documentación interactiva

| UI | URL |
|---|---|
| Swagger UI | `GET /api/v1/docs` |
| ReDoc | `GET /api/v1/redoc` |
| OpenAPI JSON | `GET /api/v1/openapi.json` |

---

## Autenticación

Todos los endpoints protegidos requieren el header:

```
Authorization: Bearer <accessToken>
```

El `accessToken` se obtiene en `POST /api/v1/auth/login`.
Duración: 30 minutos. Renovar con `POST /api/v1/auth/refresh`.

Ver [SECURITY.md](SECURITY.md) para el flujo completo.

---

## Headers

```http
Content-Type: application/json
Authorization: Bearer <accessToken>
```

---

## Formato de respuesta de error

Todos los errores retornan el mismo schema:

```json
{
  "detail": "Mensaje legible para el usuario",
  "error_code": "CODIGO_MAQUINA"
}
```

### Tabla de error_codes

| `error_code` | HTTP | Cuándo ocurre |
|---|---|---|
| `UNAUTHORIZED` | 401 | Token ausente, inválido o expirado |
| `FORBIDDEN` | 403 | Token válido pero sin permiso para este recurso |
| `NOT_FOUND` | 404 | Recurso no existe (o fue soft-deleted) |
| `CONFLICT` | 409 | Violación de unicidad o estado inconsistente |
| `UNPROCESSABLE` | 422 | Error de validación en el body del request |
| `APP_ERROR` | 400 | Error de lógica de negocio genérico |

---

## Paginación

Los listados usan cursor-based pagination para consistencia bajo escritura concurrente.

### Response

```json
{
  "data": [...],
  "next_cursor": "eyJpZCI6IjEyMyJ9",
  "has_more": true,
  "total": 150
}
```

### Query params

```
GET /api/v1/vehicles?limit=20&cursor=eyJpZCI6IjEyMyJ9
```

| Param | Default | Máximo |
|---|---|---|
| `limit` | 20 | 100 |
| `cursor` | — | — |

---

## Versionado

| Versión | Estado | Política |
|---|---|---|
| `v1` | Estable | Sin breaking changes. Nuevos campos son opcionales. |
| `v2` | Placeholder | Futuras versiones con breaking changes. |

Un endpoint deprecado en v1 permanece disponible al menos 6 meses.

---

## Endpoints por fase

### Sistema (implementado — Fase 0)

| Método | Endpoint | Auth | Descripción |
|---|---|---|---|
| `GET` | `/api/v1/health` | No | Health check v1 |
| `GET` | `/api/v2/health` | No | Health check v2 |

---

### Fase 1 — Autenticación

| Método | Endpoint | Auth | Descripción |
|---|---|---|---|
| `POST` | `/api/v1/auth/login` | No | Login con Firebase ID Token |
| `POST` | `/api/v1/auth/refresh` | Refresh Token | Renovar access token |
| `POST` | `/api/v1/auth/logout` | Sí | Revocar tokens de la sesión |
| `GET` | `/api/v1/auth/me` | Sí | Perfil del usuario autenticado |

**POST /api/v1/auth/login — Request**
```json
{ "id_token": "firebase_id_token_string" }
```

**POST /api/v1/auth/login — Response 200**
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer",
  "expires_in": 1800,
  "user": {
    "uid": "firebase_uid",
    "email": "mecanico@taller.com",
    "display_name": "Juan Pérez",
    "role": "mechanic",
    "tenant_id": "tenant_abc123"
  }
}
```

---

### Fase 2 — Gestión de Taller

| Método | Endpoint | Rol mínimo | Descripción |
|---|---|---|---|
| `POST` | `/api/v1/tenants` | — | Registrar nuevo taller |
| `GET` | `/api/v1/tenants/me` | mechanic | Perfil del taller propio |
| `PATCH` | `/api/v1/tenants/me` | admin | Actualizar perfil |
| `GET` | `/api/v1/tenants/me/users` | admin | Listar usuarios del taller |
| `POST` | `/api/v1/tenants/me/users/invite` | admin | Invitar usuario por email |
| `PATCH` | `/api/v1/tenants/me/users/{userId}` | admin | Cambiar rol de usuario |
| `DELETE` | `/api/v1/tenants/me/users/{userId}` | owner | Remover usuario del taller |

---

### Fase 3 — Vehículos

| Método | Endpoint | Rol mínimo | Descripción |
|---|---|---|---|
| `GET` | `/api/v1/vehicles` | mechanic | Listar vehículos del taller |
| `POST` | `/api/v1/vehicles` | mechanic | Registrar vehículo |
| `GET` | `/api/v1/vehicles/{id}` | mechanic | Detalle de vehículo |
| `PATCH` | `/api/v1/vehicles/{id}` | mechanic | Actualizar vehículo |
| `DELETE` | `/api/v1/vehicles/{id}` | admin | Soft delete |
| `GET` | `/api/v1/vehicles/search` | mechanic | Buscar por `?plate=` o `?vin=` |
| `GET` | `/api/v1/vehicles/{id}/inspections` | mechanic | Historial de inspecciones |

---

### Fase 4 — Inspecciones

| Método | Endpoint | Rol mínimo | Descripción |
|---|---|---|---|
| `GET` | `/api/v1/inspections` | mechanic | Listar inspecciones |
| `POST` | `/api/v1/inspections` | mechanic | Crear inspección |
| `GET` | `/api/v1/inspections/{id}` | mechanic | Detalle de inspección |
| `PATCH` | `/api/v1/inspections/{id}` | mechanic | Actualizar datos generales |
| `POST` | `/api/v1/inspections/{id}/start` | mechanic | Iniciar (draft → in_progress) |
| `POST` | `/api/v1/inspections/{id}/complete` | mechanic | Completar (in_progress → completed) |
| `GET` | `/api/v1/inspections/{id}/items` | mechanic | Items de inspección |
| `PATCH` | `/api/v1/inspections/{id}/items/{itemId}` | mechanic | Actualizar item |
| `POST` | `/api/v1/inspections/{id}/signature` | mechanic | Guardar firma digital |

---

### Fase 5 — Reportes

| Método | Endpoint | Rol mínimo | Descripción |
|---|---|---|---|
| `POST` | `/api/v1/reports` | mechanic | Generar reporte PDF |
| `GET` | `/api/v1/reports/{id}` | mechanic | Metadatos del reporte |
| `GET` | `/api/v1/reports/{id}/download` | mechanic / token público | Descargar PDF |
| `POST` | `/api/v1/reports/{id}/send` | mechanic | Enviar por email al cliente |
| `GET` | `/api/v1/reports/public/{publicToken}` | No | Acceso público por token |
