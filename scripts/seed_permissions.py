"""
Seed script: Catálogo de permisos del sistema

Crea todos los permisos en la colección global `permissions/`.
Idempotente: usa el código del permiso como ID de documento.

Uso:
    export GOOGLE_APPLICATION_CREDENTIALS=path/to/serviceAccount.json
    python scripts/seed_permissions.py [--project taller-85514]
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import click
from firebase_admin import firestore
from rich.console import Console

from utils import init_firebase

console = Console()

PERMISSIONS: list[dict] = [
    {"id": "users:read",   "module": "users", "action": "read",   "description": "Ver lista de usuarios del taller"},
    {"id": "users:create", "module": "users", "action": "create", "description": "Crear nuevos usuarios"},
    {"id": "users:update", "module": "users", "action": "update", "description": "Editar usuarios existentes"},
    {"id": "users:delete", "module": "users", "action": "delete", "description": "Desactivar usuarios (soft delete)"},

    {"id": "roles:manage", "module": "roles", "action": "manage", "description": "Crear, editar y asignar roles"},

    {"id": "tenant:read",   "module": "tenant", "action": "read",   "description": "Ver configuración del taller"},
    {"id": "tenant:manage", "module": "tenant", "action": "manage", "description": "Editar configuración, branding y plan del taller"},

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

    {"id": "templates:manage", "module": "templates", "action": "manage", "description": "Crear y editar plantillas de inspección"},

    {"id": "estimates:read",    "module": "estimates", "action": "read",    "description": "Ver presupuestos"},
    {"id": "estimates:create",  "module": "estimates", "action": "create",  "description": "Crear presupuestos"},
    {"id": "estimates:update",  "module": "estimates", "action": "update",  "description": "Editar presupuestos"},
    {"id": "estimates:send",    "module": "estimates", "action": "send",    "description": "Enviar presupuestos al cliente"},
    {"id": "estimates:convert", "module": "estimates", "action": "convert", "description": "Convertir presupuesto a orden de trabajo"},

    {"id": "work_orders:read",     "module": "work_orders", "action": "read",     "description": "Ver órdenes de trabajo"},
    {"id": "work_orders:create",   "module": "work_orders", "action": "create",   "description": "Crear órdenes de trabajo"},
    {"id": "work_orders:update",   "module": "work_orders", "action": "update",   "description": "Actualizar estado de órdenes"},
    {"id": "work_orders:complete", "module": "work_orders", "action": "complete", "description": "Marcar orden como completada"},

    {"id": "calendar:read",   "module": "calendar", "action": "read",   "description": "Ver agenda y citas"},
    {"id": "calendar:create", "module": "calendar", "action": "create", "description": "Crear eventos en la agenda"},
    {"id": "calendar:update", "module": "calendar", "action": "update", "description": "Editar eventos"},
    {"id": "calendar:delete", "module": "calendar", "action": "delete", "description": "Eliminar eventos"},

    {"id": "dashboard:read", "module": "dashboard", "action": "read",   "description": "Ver dashboard básico"},
    {"id": "reports:read",   "module": "reports",   "action": "read",   "description": "Ver reportes y KPIs"},
    {"id": "reports:export", "module": "reports",   "action": "export", "description": "Exportar reportes a CSV/Excel"},

    {"id": "notifications:manage", "module": "notifications", "action": "manage", "description": "Configurar plantillas y reglas de notificación"},

    {"id": "audit:read", "module": "audit", "action": "read", "description": "Ver logs de auditoría"},

    {"id": "api_keys:manage", "module": "api_keys", "action": "manage", "description": "Crear y revocar API keys"},
    {"id": "webhooks:manage", "module": "webhooks", "action": "manage", "description": "Configurar webhooks"},

    {"id": "pdf:generate", "module": "pdf", "action": "generate", "description": "Generar PDFs de informes y presupuestos"},
    {"id": "qr:generate",  "module": "qr",  "action": "generate", "description": "Generar y revocar códigos QR"},
]


def seed_permissions(db: firestore.Client, dry_run: bool = False) -> None:
    modules: dict[str, list[str]] = {}
    for perm in PERMISSIONS:
        modules.setdefault(perm["module"], []).append(perm["action"])

    for mod, actions in sorted(modules.items()):
        console.print(f"  [cyan]{mod}[/cyan]: {', '.join(actions)}")

    if not dry_run:
        collection = db.collection("permissions")
        for perm in PERMISSIONS:
            collection.document(perm["id"]).set(perm, merge=True)

    console.print(f"\n[bold]Total:[/bold] {len(PERMISSIONS)} permisos")


@click.command()
@click.option("--project", default="taller-85514", help="Firebase Project ID")
@click.option("--dry-run", is_flag=True, help="Mostrar sin escribir en Firestore")
def main(project: str, dry_run: bool) -> None:
    """Crea el catálogo de permisos en Firestore."""
    console.print(f"[bold]Proyecto:[/bold] {project}")
    if dry_run:
        console.print("[yellow]MODO DRY RUN — sin cambios en Firestore[/yellow]")
    db = init_firebase(project)
    console.print("\n[bold]Permisos por módulo:[/bold]")
    seed_permissions(db, dry_run=dry_run)
    console.print("\n[green]✓ Permisos creados correctamente[/green]")


if __name__ == "__main__":
    main()
