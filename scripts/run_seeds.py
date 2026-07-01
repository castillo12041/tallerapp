"""
Runner de seeds en orden correcto.

Ejecuta los 4 seeds en la secuencia que respeta las dependencias:
  1. plans       — colección global, sin dependencias
  2. permissions — colección global, sin dependencias
  3. roles       — depende de permissions (hace referencia a sus IDs)
  4. template    — independiente pero va al final por ser el más pesado

Uso:
    export GOOGLE_APPLICATION_CREDENTIALS=path/to/serviceAccount.json
    python scripts/run_seeds.py [--project taller-85514] [--dry-run]
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import click
from rich.console import Console
from rich.rule import Rule

from utils import init_firebase
from seed_plans import seed_plans
from seed_permissions import seed_permissions
from seed_roles import seed_roles
from seed_template import seed_template

console = Console()


@click.command()
@click.option("--project", default="taller-85514", help="Firebase Project ID")
@click.option("--dry-run", is_flag=True, help="Mostrar sin escribir en Firestore")
def main(project: str, dry_run: bool) -> None:
    """Ejecuta todos los seeds en orden."""
    console.print(f"[bold]Proyecto:[/bold] {project}")
    if dry_run:
        console.print("[yellow]MODO DRY RUN — sin cambios en Firestore[/yellow]")

    db = init_firebase(project)

    console.print(Rule("[cyan]1/4 Planes SaaS[/cyan]"))
    seed_plans(db, dry_run=dry_run)

    console.print(Rule("[cyan]2/4 Permisos[/cyan]"))
    seed_permissions(db, dry_run=dry_run)

    console.print(Rule("[cyan]3/4 Roles del sistema[/cyan]"))
    seed_roles(db, dry_run=dry_run)

    console.print(Rule("[cyan]4/4 Plantilla base de inspección[/cyan]"))
    seed_template(db, dry_run=dry_run)

    console.print(Rule())
    console.print("[bold green]✓ Todos los seeds completados[/bold green]")


if __name__ == "__main__":
    main()
