"""
Constantes RBAC in-memory: roles del sistema y catálogo de permisos.

Fuente de verdad compartida entre enforcement de permisos y endpoints
de solo lectura. Los seed scripts usan sus propias copias para evitar
acoplar el módulo de scripts al módulo de la app.

Cambios aquí deben reflejarse también en scripts/seed_permissions.py
y scripts/seed_roles.py.
"""

from __future__ import annotations

from typing import Final

PERMISSIONS: Final[list[dict[str, str]]] = [
    {"id": "users:read",   "module": "users",   "action": "read",     "description": "Ver lista de usuarios del taller"},
    {"id": "users:create", "module": "users",   "action": "create",   "description": "Crear nuevos usuarios"},
    {"id": "users:update", "module": "users",   "action": "update",   "description": "Editar usuarios existentes"},
    {"id": "users:delete", "module": "users",   "action": "delete",   "description": "Desactivar usuarios (soft delete)"},
    {"id": "roles:manage", "module": "roles",   "action": "manage",   "description": "Crear, editar y asignar roles"},
    {"id": "tenant:read",   "module": "tenant", "action": "read",     "description": "Ver configuración del taller"},
    {"id": "tenant:manage", "module": "tenant", "action": "manage",   "description": "Editar configuración, branding y plan del taller"},
    {"id": "clients:read",   "module": "clients", "action": "read",   "description": "Ver clientes del taller"},
    {"id": "clients:create", "module": "clients", "action": "create", "description": "Registrar nuevos clientes"},
    {"id": "clients:update", "module": "clients", "action": "update", "description": "Editar datos de clientes"},
    {"id": "clients:delete", "module": "clients", "action": "delete", "description": "Eliminar (soft delete) clientes"},
    {"id": "vehicles:read",   "module": "vehicles", "action": "read",   "description": "Ver vehículos"},
    {"id": "vehicles:create", "module": "vehicles", "action": "create", "description": "Registrar nuevos vehículos"},
    {"id": "vehicles:update", "module": "vehicles", "action": "update", "description": "Editar datos de vehículos"},
    {"id": "vehicles:delete", "module": "vehicles", "action": "delete", "description": "Eliminar vehículos"},
    {"id": "inspections:read",     "module": "inspections", "action": "read",     "description": "Ver inspecciones"},
    {"id": "inspections:create",   "module": "inspections", "action": "create",   "description": "Crear nuevas inspecciones"},
    {"id": "inspections:update",   "module": "inspections", "action": "update",   "description": "Editar inspecciones en progreso"},
    {"id": "inspections:complete", "module": "inspections", "action": "complete", "description": "Marcar inspección como completada"},
    {"id": "inspections:assign",   "module": "inspections", "action": "assign",   "description": "Asignar inspector a una inspección"},
    {"id": "inspections:review",   "module": "inspections", "action": "review",   "description": "Revisar y aprobar inspecciones"},
    {"id": "templates:manage", "module": "templates",  "action": "manage",   "description": "Crear y editar plantillas de inspección"},
    {"id": "estimates:read",    "module": "estimates", "action": "read",     "description": "Ver presupuestos"},
    {"id": "estimates:create",  "module": "estimates", "action": "create",   "description": "Crear presupuestos"},
    {"id": "estimates:update",  "module": "estimates", "action": "update",   "description": "Editar presupuestos"},
    {"id": "estimates:send",    "module": "estimates", "action": "send",     "description": "Enviar presupuestos al cliente"},
    {"id": "estimates:convert", "module": "estimates", "action": "convert",  "description": "Convertir presupuesto a orden de trabajo"},
    {"id": "work_orders:read",     "module": "work_orders", "action": "read",     "description": "Ver órdenes de trabajo"},
    {"id": "work_orders:create",   "module": "work_orders", "action": "create",   "description": "Crear órdenes de trabajo"},
    {"id": "work_orders:update",   "module": "work_orders", "action": "update",   "description": "Actualizar estado de órdenes"},
    {"id": "work_orders:complete", "module": "work_orders", "action": "complete", "description": "Marcar orden como completada"},
    {"id": "calendar:read",   "module": "calendar", "action": "read",   "description": "Ver agenda y citas"},
    {"id": "calendar:create", "module": "calendar", "action": "create", "description": "Crear eventos en la agenda"},
    {"id": "calendar:update", "module": "calendar", "action": "update", "description": "Editar eventos"},
    {"id": "calendar:delete", "module": "calendar", "action": "delete", "description": "Eliminar eventos"},
    {"id": "dashboard:read",        "module": "dashboard",       "action": "read",     "description": "Ver dashboard básico"},
    {"id": "reports:read",          "module": "reports",         "action": "read",     "description": "Ver reportes y KPIs"},
    {"id": "reports:export",        "module": "reports",         "action": "export",   "description": "Exportar reportes a CSV/Excel"},
    {"id": "notifications:manage",  "module": "notifications",   "action": "manage",   "description": "Configurar plantillas y reglas de notificación"},
    {"id": "audit:read",            "module": "audit",           "action": "read",     "description": "Ver logs de auditoría"},
    {"id": "api_keys:manage",       "module": "api_keys",        "action": "manage",   "description": "Crear y revocar API keys"},
    {"id": "webhooks:manage",       "module": "webhooks",        "action": "manage",   "description": "Configurar webhooks"},
    {"id": "pdf:generate",          "module": "pdf",             "action": "generate", "description": "Generar PDFs de informes y presupuestos"},
    {"id": "qr:generate",           "module": "qr",              "action": "generate", "description": "Generar y revocar códigos QR"},
]

SYSTEM_ROLES: Final[list[dict]] = [
    {
        "code": "superadmin",
        "name": "Super Administrador",
        "description": "Acceso total a la plataforma. No pertenece a ningún taller.",
        "is_system": True,
        "can_be_assigned": False,
        "display_order": 0,
        "permissions": ["*"],
    },
    {
        "code": "tenantadmin",
        "name": "Administrador del Taller",
        "description": "Control total sobre su taller: usuarios, configuración, facturación.",
        "is_system": True,
        "can_be_assigned": True,
        "display_order": 1,
        "permissions": [
            "users:read", "users:create", "users:update", "users:delete",
            "roles:manage", "tenant:read", "tenant:manage",
            "clients:read", "clients:create", "clients:update", "clients:delete",
            "vehicles:read", "vehicles:create", "vehicles:update", "vehicles:delete",
            "inspections:read", "inspections:create", "inspections:update",
            "inspections:complete", "inspections:assign", "inspections:review",
            "templates:manage",
            "estimates:read", "estimates:create", "estimates:update",
            "estimates:send", "estimates:convert",
            "work_orders:read", "work_orders:create", "work_orders:update", "work_orders:complete",
            "calendar:read", "calendar:create", "calendar:update", "calendar:delete",
            "dashboard:read", "reports:read", "reports:export",
            "notifications:manage", "audit:read", "api_keys:manage", "webhooks:manage",
            "pdf:generate", "qr:generate",
        ],
    },
    {
        "code": "workshopmanager",
        "name": "Gerente de Taller",
        "description": "Gestión operativa del taller. Sin acceso a configuración ni facturación.",
        "is_system": True,
        "can_be_assigned": True,
        "display_order": 2,
        "permissions": [
            "users:read",
            "clients:read", "clients:create", "clients:update",
            "vehicles:read", "vehicles:create", "vehicles:update",
            "inspections:read", "inspections:create", "inspections:update",
            "inspections:complete", "inspections:assign", "inspections:review",
            "templates:manage",
            "estimates:read", "estimates:create", "estimates:update",
            "estimates:send", "estimates:convert",
            "work_orders:read", "work_orders:create", "work_orders:update", "work_orders:complete",
            "calendar:read", "calendar:create", "calendar:update", "calendar:delete",
            "dashboard:read", "reports:read", "reports:export",
            "notifications:manage", "pdf:generate", "qr:generate",
        ],
    },
    {
        "code": "inspector",
        "name": "Inspector",
        "description": "Realiza inspecciones precompra. Acceso a su cartera de inspecciones.",
        "is_system": True,
        "can_be_assigned": True,
        "display_order": 3,
        "permissions": [
            "clients:read",
            "vehicles:read", "vehicles:create",
            "inspections:read", "inspections:create", "inspections:update", "inspections:complete",
            "calendar:read", "dashboard:read", "pdf:generate",
        ],
    },
    {
        "code": "mechanic",
        "name": "Mecánico",
        "description": "Ejecuta órdenes de trabajo asignadas.",
        "is_system": True,
        "can_be_assigned": True,
        "display_order": 4,
        "permissions": [
            "clients:read", "vehicles:read", "inspections:read",
            "work_orders:read", "work_orders:update", "work_orders:complete",
            "calendar:read",
        ],
    },
    {
        "code": "receptionist",
        "name": "Recepcionista",
        "description": "Gestión de clientes, vehículos, agenda y recepción de trabajos.",
        "is_system": True,
        "can_be_assigned": True,
        "display_order": 5,
        "permissions": [
            "clients:read", "clients:create", "clients:update",
            "vehicles:read", "vehicles:create", "vehicles:update",
            "inspections:read", "inspections:create",
            "estimates:read", "estimates:send",
            "work_orders:read",
            "calendar:read", "calendar:create", "calendar:update",
            "dashboard:read",
        ],
    },
    {
        "code": "customer",
        "name": "Cliente",
        "description": "Acceso al portal del cliente. Solo puede ver sus propios datos.",
        "is_system": True,
        "can_be_assigned": True,
        "display_order": 6,
        "permissions": [],
    },
]

# Maps role code → default permissions list
ROLE_PERMISSIONS: Final[dict[str, list[str]]] = {
    role["code"]: role["permissions"]
    for role in SYSTEM_ROLES
}

# Roles that can be assigned to users within a tenant
ASSIGNABLE_ROLES: Final[set[str]] = {
    role["code"] for role in SYSTEM_ROLES if role.get("can_be_assigned", False)
}
