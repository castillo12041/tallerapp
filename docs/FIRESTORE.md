# Modelo de Datos — Firestore Completo

> Fuente oficial del esquema de datos. Ver [FIRESTORE_SCHEMAS.md](FIRESTORE_SCHEMAS.md) para schemas de campos completos.

## Principios de Diseño

1. **tenantId obligatorio** en todos los documentos sin excepción
2. **Campos de auditoría** en todo documento mutable: `createdAt`, `updatedAt`, `createdBy`, `updatedBy`, `deletedAt`
3. **Soft Delete** en todas las colecciones críticas (`deletedAt` timestamp)
4. **Desnormalización controlada** — datos de lectura frecuente duplicados para evitar joins
5. **Snapshots inmutables** — en inspecciones y reportes, datos del vehículo/cliente se copian al momento de creación
6. **Contadores denormalizados** — `inspectionCount`, `storageUsedBytes` para dashboard sin queries costosos
7. **Índices compuestos** — siempre `tenantId` como primer campo del índice compuesto
8. **Append-only** — audit_logs nunca se modifican ni eliminan

---

## Mapa de Colecciones

```
tallerapp (Firestore)
│
├── tenants/                    # Un doc por taller (tenant)
├── plans/                      # Planes SaaS (global, no por tenant)
├── subscriptions/              # Suscripción activa por tenant
│
├── users/                      # Usuarios de la plataforma
├── roles/                      # Roles por tenant + roles de sistema
├── permissions/                # Definición de permisos (global)
│
├── clients/                    # Clientes del taller
├── vehicles/                   # Vehículos registrados
├── vehicle_history/            # Log de cambios de vehículos
│
├── inspection_templates/       # Plantillas de inspección
├── inspections/                # Inspecciones realizadas
│   └── {id}/items/             # Items de cada inspección (subcolección)
├── inspection_photos/          # Metadata de fotos (root para analytics)
├── inspection_audio/           # Metadata de audio
├── inspection_signatures/      # Firmas digitales
│
├── estimates/                  # Presupuestos
├── estimate_items/             # Items de presupuestos (root)
├── work_orders/                # Órdenes de trabajo
├── work_order_items/           # Items de OT (root)
│
├── calendar/                   # Eventos de agenda
├── notifications/              # Notificaciones por usuario
│
├── emails/                     # Registro de emails enviados
├── whatsapp_messages/          # Registro de mensajes WA
│
├── reports/                    # Reportes PDF generados
├── public_tokens/              # Tokens firmados para acceso público
│
├── storage_files/              # Metadata de archivos en Firebase Storage
├── settings/                   # Configuración por tenant
│
├── api_keys/                   # API keys para acceso programático
├── webhooks/                   # Configuración de webhooks
│
└── audit_logs/                 # Log de auditoría (append-only, nunca borrar)
```

---

## Campos de Auditoría (Obligatorios en Todo Documento)

```typescript
{
  tenantId:   string       // ID del taller (nunca null excepto en collections globales)
  createdAt:  Timestamp    // Momento de creación (inmutable)
  updatedAt:  Timestamp    // Última modificación
  createdBy:  string       // UID Firebase del creador (inmutable)
  updatedBy:  string       // UID Firebase del último editor
  deletedAt:  Timestamp?   // null = activo | timestamp = soft deleted
}
```

---

## Colecciones Globales (Sin tenantId)

### `plans/{planId}`

Definición de los planes SaaS. Modificado solo por SuperAdmin.

| Campo | Tipo | Notas |
|---|---|---|
| `code` | enum | `basic` · `professional` · `premium` · `enterprise` |
| `name` | string | Nombre para display |
| `price` | number | Precio mensual (CLP) |
| `annualPrice` | number | Precio anual con descuento |
| `features` | map | Ver [SUBSCRIPTIONS.md](SUBSCRIPTIONS.md) para feature flags completos |
| `isActive` | boolean | Si se ofrece activamente |
| `sortOrder` | number | Orden en la UI |

### `permissions/{permissionId}`

Catálogo de todos los permisos del sistema. Global, inmutable una vez publicado.

| Campo | Tipo | Notas |
|---|---|---|
| `code` | string | Unique: `inspection:create`, `vehicle:delete` |
| `module` | string | `inspection`, `vehicle`, `client`, etc. |
| `action` | string | `view`, `create`, `edit`, `delete`, etc. |
| `description` | string | Descripción legible |

---

## Colecciones por Tenant

### `tenants/{tenantId}` — El Taller

| Campo | Tipo | Notas |
|---|---|---|
| `name` | string | Nombre del taller |
| `slug` | string | URL slug único |
| `subdomain` | string? | Subdominio personalizado |
| `customDomain` | string? | Dominio propio (Premium+) |
| `rut` | string | RUT empresarial |
| `planId` | string | Referencia al plan activo |
| `subscriptionId` | string | Referencia a la suscripción |
| `subscriptionStatus` | enum | `trialing·active·past_due·cancelled` |
| `branding` | map | `{primaryColor, secondaryColor, logoUrl, ...}` |
| `settings` | map | `{timezone, locale, currency, autoSendPdf, ...}` |
| `storageUsedBytes` | number | Denormalizado para limits |
| `inspectionCountThisMonth` | number | Denormalizado para límite de plan |
| `activeUserCount` | number | Denormalizado |
| `isActive` | boolean | |
| `isSuspended` | boolean | |

### `subscriptions/{subscriptionId}`

| Campo | Tipo | Notas |
|---|---|---|
| `tenantId` | string | |
| `planId` | string | |
| `status` | enum | `trialing·active·past_due·cancelled·expired` |
| `currentPeriodStart` | Timestamp | |
| `currentPeriodEnd` | Timestamp | |
| `trialEndsAt` | Timestamp? | |
| `cancelledAt` | Timestamp? | |
| `amount` | number | |
| `currency` | string | |

### `users/{userId}` — Usuario

`userId` = UID de Firebase Auth

| Campo | Tipo | Notas |
|---|---|---|
| `tenantId` | string | |
| `email` | string | |
| `displayName` | string | |
| `firstName` | string | |
| `lastName` | string | |
| `phone` | string? | |
| `role` | string | ID del rol asignado |
| `permissions` | string[] | Permisos override (sobre el rol) |
| `isActive` | boolean | |
| `lastLoginAt` | Timestamp? | |
| `fcmTokens` | string[] | Para push notifications |
| `preferences` | map | `{language, timezone, notifications:{email,push,wa}}` |

### `roles/{roleId}`

| Campo | Tipo | Notas |
|---|---|---|
| `tenantId` | string? | null = rol de sistema |
| `code` | string | Único por tenant: `inspector`, `mechanic`, etc. |
| `name` | string | |
| `permissions` | string[] | Códigos de permisos: `['inspection:create', ...]` |
| `isSystem` | boolean | Los roles de sistema no se pueden eliminar |

### `clients/{clientId}`

| Campo | Tipo | Notas |
|---|---|---|
| `tenantId` | string | |
| `firstName` | string | |
| `lastName` | string | |
| `fullName` | string | Desnormalizado para búsqueda |
| `email` | string? | |
| `phone` | string? | |
| `whatsapp` | string? | |
| `rut` | string? | RUT del cliente |
| `vehicleCount` | number | Denormalizado |
| `inspectionCount` | number | Denormalizado |
| `totalSpent` | number | Denormalizado |
| `lastInteractionAt` | Timestamp? | |

### `vehicles/{vehicleId}`

| Campo | Tipo | Notas |
|---|---|---|
| `tenantId` | string | |
| `clientId` | string? | |
| `plate` | string | Normalizada: `ABCD12` (sin guión, mayúsculas) |
| `vin` | string? | |
| `brand` | string | |
| `model` | string | |
| `year` | number | |
| `version` | string? | Versión/trim |
| `mileage` | number? | |
| `fuelType` | enum | `gasoline·diesel·electric·hybrid·gas` |
| `transmission` | enum? | `manual·automatic·cvt` |
| `color` | string? | |
| `clientName` | string? | Desnormalizado |
| `inspectionCount` | number | Desnormalizado |
| `lastInspectionAt` | Timestamp? | |

### `inspections/{inspectionId}`

| Campo | Tipo | Notas |
|---|---|---|
| `tenantId` | string | |
| `number` | string | `INS-2024-001234` |
| `vehicleId` | string | |
| `clientId` | string? | |
| `mechanicId` | string | |
| `templateId` | string? | |
| `status` | enum | `draft·in_progress·review·completed·cancelled` |
| `vehicleSnapshot` | map | Copia inmutable del vehículo al crear |
| `clientSnapshot` | map | Copia inmutable del cliente |
| `tenantSnapshot` | map | Copia del taller para PDF sin joins |
| `mileageAtInspection` | number? | |
| `fuelLevel` | enum? | `empty·1/4·1/2·3/4·full` |
| `totalItems` | number | |
| `goodItems` | number | |
| `regularItems` | number | |
| `badItems` | number | |
| `naItems` | number | |
| `score` | number? | 0-100 calculado al completar |
| `totalRepairCost` | number | |
| `currency` | string | |
| `generalObservations` | string? | |
| `recommendations` | string? | |
| `clientSignatureUrl` | string? | |
| `reportUrl` | string? | |
| `publicToken` | string? | Token HMAC para acceso público |
| `publicTokenExpiresAt` | Timestamp? | |
| `reportSentByEmail` | boolean | |
| `reportSentByWhatsapp` | boolean | |
| `isOffline` | boolean | Fue creada offline |
| `syncedAt` | Timestamp? | |
| `startedAt` | Timestamp? | |
| `completedAt` | Timestamp? | |

### `inspections/{id}/items/{itemId}` — Punto de Inspección

Subcollección de la inspección padre.

| Campo | Tipo | Notas |
|---|---|---|
| `tenantId` | string | |
| `inspectionId` | string | |
| `category` | string | `Motor`, `Frenos`, `Carrocería`, etc. |
| `categoryOrder` | number | |
| `name` | string | Nombre del punto |
| `order` | number | Orden dentro de la categoría |
| `status` | enum | `pending·good·regular·bad·na` |
| `observation` | string? | |
| `repairCost` | number? | |
| `photoUrls` | string[] | URLs en Firebase Storage |
| `audioUrl` | string? | |
| `photoCount` | number | Desnormalizado |
| `latitude` | number? | GPS opcional |
| `longitude` | number? | GPS opcional |
| `ai_suggestions` | map? | Preparado para IA (no implementado) |
| `isOffline` | boolean | |
| `localPhotoIds` | string[] | IDs locales pendientes de upload |

### `inspection_templates/{templateId}`

| Campo | Tipo | Notas |
|---|---|---|
| `tenantId` | string? | null = plantilla del sistema |
| `name` | string | |
| `version` | number | |
| `isDefault` | boolean | |
| `categories` | array | `[{id, name, order, items:[{id, name, order, ...}]}]` |
| `totalItemCount` | number | |

### `estimates/{estimateId}` y `work_orders/{orderId}`

Ver [FIRESTORE_SCHEMAS.md](FIRESTORE_SCHEMAS.md) para schema completo.

### `public_tokens/{tokenId}`

| Campo | Tipo | Notas |
|---|---|---|
| `tenantId` | string | |
| `token` | string | Token completo (indexado) |
| `tokenHash` | string | SHA-256 para lookup rápido |
| `entityType` | string | `inspection·estimate·report` |
| `entityId` | string | |
| `permissions` | string[] | Qué puede hacer el portador |
| `expiresAt` | Timestamp | |
| `isRevoked` | boolean | |
| `accessCount` | number | |
| `lastAccessAt` | Timestamp? | |

### `audit_logs/{logId}` — INMUTABLE

| Campo | Tipo | Notas |
|---|---|---|
| `tenantId` | string? | null para acciones de sistema |
| `userId` | string | |
| `userEmail` | string | Desnormalizado |
| `userRole` | string | Desnormalizado |
| `action` | string | `inspection.create`, `user.delete`, etc. |
| `entityType` | string | Colección afectada |
| `entityId` | string | |
| `ipAddress` | string | |
| `userAgent` | string | |
| `requestId` | string | UUID del request HTTP |
| `before` | map? | Estado anterior (null en creates) |
| `after` | map? | Estado nuevo (null en deletes) |
| `changes` | string[] | Campos que cambiaron |
| `severity` | enum | `info·warning·critical` |
| `createdAt` | Timestamp | |

---

## Índices Compuestos Requeridos

| Colección | Campo 1 | Campo 2 | Campo 3 | Uso |
|---|---|---|---|---|
| `users` | `tenantId` | `isActive` | `role` | Listar usuarios activos por rol |
| `vehicles` | `tenantId` | `plate` | — | Buscar por patente |
| `vehicles` | `tenantId` | `clientId` | `createdAt` DESC | Vehículos de un cliente |
| `vehicles` | `tenantId` | `deletedAt` | `createdAt` DESC | Listar activos paginados |
| `inspections` | `tenantId` | `status` | `createdAt` DESC | Por estado |
| `inspections` | `tenantId` | `mechanicId` | `createdAt` DESC | Del mecánico |
| `inspections` | `tenantId` | `vehicleId` | `createdAt` DESC | Historial vehículo |
| `inspections` | `tenantId` | `deletedAt` | `createdAt` DESC | Activas paginadas |
| `clients` | `tenantId` | `fullName` | — | Búsqueda por nombre |
| `estimates` | `tenantId` | `status` | `createdAt` DESC | Por estado |
| `work_orders` | `tenantId` | `status` | `startedAt` | En progreso |
| `calendar` | `tenantId` | `assignedToId` | `startAt` | Agenda del usuario |
| `notifications` | `userId` | `isRead` | `createdAt` DESC | Sin leer por usuario |
| `audit_logs` | `tenantId` | `entityType` | `createdAt` DESC | Auditoría por entidad |
| `public_tokens` | `token` | — | — | Verificar token público |
| `refresh_tokens` | `userId` | `expiresAt` | — | Validar y limpiar |

---

## Outline de Firestore Security Rules

```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {

    // Plans y permissions: solo lectura global
    match /plans/{planId} {
      allow read: if request.auth != null;
      allow write: if false; // Solo Admin SDK
    }

    match /permissions/{permId} {
      allow read: if request.auth != null;
      allow write: if false;
    }

    // Toda colección por tenant: solo el mismo tenant
    function isAuthenticated() {
      return request.auth != null;
    }

    function belongsToTenant(tenantId) {
      return request.auth.token.tenant_id == tenantId;
    }

    function hasPermission(perm) {
      return perm in request.auth.token.permissions;
    }

    // Ejemplo patrón para colecciones tenant-scoped:
    match /inspections/{docId} {
      allow read: if isAuthenticated()
        && belongsToTenant(resource.data.tenantId)
        && hasPermission('inspection:view');
      allow write: if false; // Siempre via backend (Admin SDK)
    }

    // audit_logs: solo lectura para auditores
    match /audit_logs/{logId} {
      allow read: if isAuthenticated()
        && hasPermission('audit:view');
      allow write: if false; // Solo backend
    }

    // Default: denegar todo
    match /{document=**} {
      allow read, write: if false;
    }
  }
}
```

**Nota:** El backend usa Admin SDK (bypass rules). Las Rules son defensa en profundidad para acceso directo desde los clientes Firebase SDK.
