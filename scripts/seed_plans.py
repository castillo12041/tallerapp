"""
Seed script: Planes SaaS

Crea los 4 planes en la colección global `plans/`.
Idempotente: usa el código del plan como ID de documento.

Uso:
    export GOOGLE_APPLICATION_CREDENTIALS=path/to/serviceAccount.json
    python scripts/seed_plans.py [--project taller-85514]
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

PLANS: list[dict] = [
    {
        "id": "basic",
        "code": "basic",
        "name": "Basic",
        "displayOrder": 1,
        "price": {"monthly": 0, "annual": 0, "currency": "CLP"},
        "trialDays": 14,
        "features": {
            "maxUsers": 2,
            "maxInspectionsPerMonth": 20,
            "maxStorageGB": 1,
            "maxClients": 50,
            "maxTemplates": 1,
            "clientPortal": False,
            "estimates": False,
            "workOrders": False,
            "calendar": False,
            "advancedDashboard": False,
            "customBranding": False,
            "customDomain": False,
            "whatsappIntegration": False,
            "publicApi": False,
            "webhooks": False,
            "aiFeatures": False,
            "dataExport": False,
            "prioritySupport": False,
            "dedicatedSupport": False,
        },
        "isActive": True,
    },
    {
        "id": "professional",
        "code": "professional",
        "name": "Professional",
        "displayOrder": 2,
        "price": {"monthly": 29990, "annual": 299990, "currency": "CLP"},
        "trialDays": 14,
        "features": {
            "maxUsers": 5,
            "maxInspectionsPerMonth": 100,
            "maxStorageGB": 10,
            "maxClients": 500,
            "maxTemplates": 5,
            "clientPortal": True,
            "estimates": True,
            "workOrders": True,
            "calendar": True,
            "advancedDashboard": True,
            "customBranding": False,
            "customDomain": False,
            "whatsappIntegration": False,
            "publicApi": False,
            "webhooks": False,
            "aiFeatures": False,
            "dataExport": True,
            "prioritySupport": False,
            "dedicatedSupport": False,
        },
        "isActive": True,
    },
    {
        "id": "premium",
        "code": "premium",
        "name": "Premium",
        "displayOrder": 3,
        "price": {"monthly": 79990, "annual": 799990, "currency": "CLP"},
        "trialDays": 14,
        "features": {
            "maxUsers": 15,
            "maxInspectionsPerMonth": 500,
            "maxStorageGB": 50,
            "maxClients": 5000,
            "maxTemplates": 20,
            "clientPortal": True,
            "estimates": True,
            "workOrders": True,
            "calendar": True,
            "advancedDashboard": True,
            "customBranding": True,
            "customDomain": True,
            "whatsappIntegration": True,
            "publicApi": False,
            "webhooks": False,
            "aiFeatures": False,
            "dataExport": True,
            "prioritySupport": True,
            "dedicatedSupport": False,
        },
        "isActive": True,
    },
    {
        "id": "enterprise",
        "code": "enterprise",
        "name": "Enterprise",
        "displayOrder": 4,
        "price": {"monthly": -1, "annual": -1, "currency": "CLP"},
        "trialDays": 30,
        "features": {
            "maxUsers": -1,
            "maxInspectionsPerMonth": -1,
            "maxStorageGB": -1,
            "maxClients": -1,
            "maxTemplates": -1,
            "clientPortal": True,
            "estimates": True,
            "workOrders": True,
            "calendar": True,
            "advancedDashboard": True,
            "customBranding": True,
            "customDomain": True,
            "whatsappIntegration": True,
            "publicApi": True,
            "webhooks": True,
            "aiFeatures": True,
            "dataExport": True,
            "prioritySupport": True,
            "dedicatedSupport": True,
        },
        "isActive": True,
    },
]


def seed_plans(db: firestore.Client, dry_run: bool = False) -> None:
    collection = db.collection("plans")

    table = Table(title="Planes SaaS")
    table.add_column("ID", style="cyan")
    table.add_column("Nombre")
    table.add_column("Precio Mensual")
    table.add_column("Usuarios")
    table.add_column("Inspecciones/mes")
    table.add_column("Estado")

    for plan in PLANS:
        plan_id = plan["id"]
        price = plan["price"]["monthly"]
        price_str = "A convenir" if price == -1 else f"${price:,} CLP"
        max_users = plan["features"]["maxUsers"]
        users_str = "Ilimitados" if max_users == -1 else str(max_users)
        max_insp = plan["features"]["maxInspectionsPerMonth"]
        insp_str = "Ilimitadas" if max_insp == -1 else str(max_insp)

        if not dry_run:
            collection.document(plan_id).set(plan, merge=True)

        table.add_row(
            plan_id, plan["name"], price_str, users_str, insp_str,
            "DRY RUN" if dry_run else "CREADO",
        )

    console.print(table)


@click.command()
@click.option("--project", default="taller-85514", help="Firebase Project ID")
@click.option("--dry-run", is_flag=True, help="Mostrar sin escribir en Firestore")
def main(project: str, dry_run: bool) -> None:
    """Crea los planes SaaS en Firestore."""
    console.print(f"[bold]Proyecto:[/bold] {project}")
    if dry_run:
        console.print("[yellow]MODO DRY RUN — sin cambios en Firestore[/yellow]")
    db = init_firebase(project)
    seed_plans(db, dry_run=dry_run)
    console.print("[green]✓ Planes creados correctamente[/green]")


if __name__ == "__main__":
    main()
