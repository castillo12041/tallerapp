"""
Seed script: Roles del sistema

Crea los roles canónicos en la colección global `roles/`.
Idempotente: usa el código del rol como ID de documento.

Nota: Los roles de cada taller se crean al registrar el tenant,
copiando estos roles base.

Uso:
    export GOOGLE_APPLICATION_CREDENTIALS=path/to/serviceAccount.json
    python scripts/seed_roles.py [--project taller-85514]
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import click
from firebase_admin import firestore
from rich.console import Console
from rich.table import Table

from utils import init_firebase

console = Console()

SYSTEM_ROLES: list[dict] = [
    {
        "id": "superadmin",
        "code": "superadmin",
        "name": "Super Administrador",
        "description": "Acceso total a la plataforma. No pertenece a ningún taller.",
        "isSystem": True,
        "tenantId": None,
        "permissions": ["*"],
        "canBeAssigned": False,
        "displayOrder": 0,
    },
    {
        "id": "tenantadmin",
        "code": "tenantadmin",
        "name": "Administrador del Taller",
        "description": "Control total sobre su taller: usuarios, configuración, facturación.",
        "isSystem": True,
        "tenantId": None,
        "permissions": [
            "users:read", "users:create", "users:update", "users:delete",
            "roles:manage",
            "tenant:read", "tenant:manage",
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
            "notifications:manage",
            "audit:read",
            "api_keys:manage",
            "webhooks:manage",
            "pdf:generate", "qr:generate",
        ],
        "canBeAssigned": True,
        "displayOrder": 1,
    },
    {
        "id": "workshopmanager",
        "code": "workshopmanager",
        "name": "Gerente de Taller",
        "description": "Gestión operativa del taller. Sin acceso a configuración ni facturación.",
        "isSystem": True,
        "tenantId": None,
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
            "notifications:manage",
            "pdf:generate", "qr:generate",
        ],
        "canBeAssigned": True,
        "displayOrder": 2,
    },
    {
        "id": "inspector",
        "code": "inspector",
        "name": "Inspector",
        "description": "Realiza inspecciones precompra. Acceso a su cartera de inspecciones.",
        "isSystem": True,
        "tenantId": None,
        "permissions": [
            "clients:read",
            "vehicles:read", "vehicles:create",
            "inspections:read", "inspections:create", "inspections:update", "inspections:complete",
            "calendar:read",
            "dashboard:read",
            "pdf:generate",
        ],
        "canBeAssigned": True,
        "displayOrder": 3,
    },
    {
        "id": "mechanic",
        "code": "mechanic",
        "name": "Mecánico",
        "description": "Ejecuta órdenes de trabajo asignadas.",
        "isSystem": True,
        "tenantId": None,
        "permissions": [
            "clients:read",
            "vehicles:read",
            "inspections:read",
            "work_orders:read", "work_orders:update", "work_orders:complete",
            "calendar:read",
        ],
        "canBeAssigned": True,
        "displayOrder": 4,
    },
    {
        "id": "receptionist",
        "code": "receptionist",
        "name": "Recepcionista",
        "description": "Gestión de clientes, vehículos, agenda y recepción de trabajos.",
        "isSystem": True,
        "tenantId": None,
        "permissions": [
            "clients:read", "clients:create", "clients:update",
            "vehicles:read", "vehicles:create", "vehicles:update",
            "inspections:read", "inspections:create",
            "estimates:read", "estimates:send",
            "work_orders:read",
            "calendar:read", "calendar:create", "calendar:update",
            "dashboard:read",
        ],
        "canBeAssigned": True,
        "displayOrder": 5,
    },
    {
        "id": "customer",
        "code": "customer",
        "name": "Cliente",
        "description": "Acceso al portal del cliente. Solo puede ver sus propios datos.",
        "isSystem": True,
        "tenantId": None,
        "permissions": [],
        "canBeAssigned": True,
        "displayOrder": 6,
    },
]


def seed_roles(db: firestore.Client, dry_run: bool = False) -> None:
    collection = db.collection("roles")

    table = Table(title="Roles del Sistema")
    table.add_column("Código", style="cyan")
    table.add_column("Nombre")
    table.add_column("Permisos")
    table.add_column("Estado")

    for role in SYSTEM_ROLES:
        perms = role["permissions"]
        perm_count = "Todos (*)" if perms == ["*"] else str(len(perms))

        if not dry_run:
            collection.document(role["id"]).set(role, merge=True)

        table.add_row(
            role["code"], role["name"], perm_count,
            "DRY RUN" if dry_run else "CREADO",
        )

    console.print(table)


@click.command()
@click.option("--project", default="taller-85514", help="Firebase Project ID")
@click.option("--dry-run", is_flag=True, help="Mostrar sin escribir en Firestore")
def main(project: str, dry_run: bool) -> None:
    """Crea los roles del sistema en Firestore."""
    console.print(f"[bold]Proyecto:[/bold] {project}")
    if dry_run:
        console.print("[yellow]MODO DRY RUN — sin cambios en Firestore[/yellow]")
    db = init_firebase(project)
    seed_roles(db, dry_run=dry_run)
    console.print("[green]✓ Roles creados correctamente[/green]")


if __name__ == "__main__":
    main()
