"""
Seed script: Plantilla base de inspección precompra

Crea la plantilla canónica con 15 secciones y 152 puntos de inspección.
Se crea en la colección `inspection_templates/` con tenantId = "__system__"
para que pueda ser clonada al registrar cada taller.

Uso:
    export GOOGLE_APPLICATION_CREDENTIALS=path/to/serviceAccount.json
    python scripts/seed_template.py [--project taller-85514]
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import click
from firebase_admin import firestore
from rich.console import Console
from rich.table import Table

from utils import init_firebase

console = Console()

SYSTEM_TENANT = "__system__"
TEMPLATE_ID = "base_precompra_v1"

SECTIONS: list[dict] = [
    {
        "id": "exterior",
        "name": "Exterior / Carrocería",
        "order": 1,
        "icon": "car_outlined",
        "items": [
            {"id": "ext_01", "name": "Panel frontal / capó",                  "requiresPhoto": True,  "requiresComment": False},
            {"id": "ext_02", "name": "Panel trasero / maletero",               "requiresPhoto": True,  "requiresComment": False},
            {"id": "ext_03", "name": "Guardabarro delantero izquierdo",        "requiresPhoto": True,  "requiresComment": False},
            {"id": "ext_04", "name": "Guardabarro delantero derecho",          "requiresPhoto": True,  "requiresComment": False},
            {"id": "ext_05", "name": "Guardabarro trasero izquierdo",          "requiresPhoto": True,  "requiresComment": False},
            {"id": "ext_06", "name": "Guardabarro trasero derecho",            "requiresPhoto": True,  "requiresComment": False},
            {"id": "ext_07", "name": "Puerta delantera izquierda",             "requiresPhoto": True,  "requiresComment": False},
            {"id": "ext_08", "name": "Puerta delantera derecha",               "requiresPhoto": True,  "requiresComment": False},
            {"id": "ext_09", "name": "Puerta trasera izquierda",               "requiresPhoto": True,  "requiresComment": False},
            {"id": "ext_10", "name": "Puerta trasera derecha",                 "requiresPhoto": True,  "requiresComment": False},
            {"id": "ext_11", "name": "Techo / techo corredizo",                "requiresPhoto": True,  "requiresComment": False},
            {"id": "ext_12", "name": "Paragolpes delantero",                   "requiresPhoto": True,  "requiresComment": False},
            {"id": "ext_13", "name": "Paragolpes trasero",                     "requiresPhoto": True,  "requiresComment": False},
            {"id": "ext_14", "name": "Pintura general (brillo, uniformidad)",  "requiresPhoto": True,  "requiresComment": True},
            {"id": "ext_15", "name": "Parabrisas delantero (fisuras/impactos)","requiresPhoto": True,  "requiresComment": True},
            {"id": "ext_16", "name": "Vidrio trasero",                         "requiresPhoto": False, "requiresComment": True},
            {"id": "ext_17", "name": "Vidrios laterales",                      "requiresPhoto": False, "requiresComment": False},
            {"id": "ext_18", "name": "Molduras, emblemas y cromados",          "requiresPhoto": False, "requiresComment": False},
            {"id": "ext_19", "name": "Sellos y burletes de puertas",           "requiresPhoto": False, "requiresComment": False},
        ],
    },
    {
        "id": "interior",
        "name": "Interior",
        "order": 2,
        "icon": "airline_seat_recline_extra",
        "items": [
            {"id": "int_01", "name": "Panel de instrumentos / tablero",              "requiresPhoto": True,  "requiresComment": False},
            {"id": "int_02", "name": "Volante (estado y deformación de airbag)",     "requiresPhoto": False, "requiresComment": True},
            {"id": "int_03", "name": "Asiento del conductor",                        "requiresPhoto": True,  "requiresComment": False},
            {"id": "int_04", "name": "Asiento del acompañante",                      "requiresPhoto": True,  "requiresComment": False},
            {"id": "int_05", "name": "Asientos traseros",                            "requiresPhoto": True,  "requiresComment": False},
            {"id": "int_06", "name": "Cinturones de seguridad (todos)",              "requiresPhoto": False, "requiresComment": True},
            {"id": "int_07", "name": "Alfombrillas y tapizado de piso",              "requiresPhoto": False, "requiresComment": False},
            {"id": "int_08", "name": "Palanca de cambios / selectora",               "requiresPhoto": False, "requiresComment": False},
            {"id": "int_09", "name": "Climatizador / aire acondicionado / calefacción","requiresPhoto": False,"requiresComment": True},
            {"id": "int_10", "name": "Maletero / compartimiento de carga",           "requiresPhoto": True,  "requiresComment": False},
            {"id": "int_11", "name": "Iluminación interior",                         "requiresPhoto": False, "requiresComment": False},
            {"id": "int_12", "name": "Guantera y apoyabrazos",                       "requiresPhoto": False, "requiresComment": False},
        ],
    },
    {
        "id": "motor",
        "name": "Motor",
        "order": 3,
        "icon": "settings",
        "items": [
            {"id": "mot_01", "name": "Nivel y calidad del aceite de motor",    "requiresPhoto": False, "requiresComment": True},
            {"id": "mot_02", "name": "Nivel de refrigerante (anticongelante)", "requiresPhoto": False, "requiresComment": True},
            {"id": "mot_03", "name": "Nivel de líquido de frenos",             "requiresPhoto": False, "requiresComment": True},
            {"id": "mot_04", "name": "Nivel de líquido dirección hidráulica",  "requiresPhoto": False, "requiresComment": True, "defaultStatus": "na"},
            {"id": "mot_05", "name": "Nivel de líquido de embrague",           "requiresPhoto": False, "requiresComment": True, "defaultStatus": "na"},
            {"id": "mot_06", "name": "Correa de distribución / cadena",        "requiresPhoto": True,  "requiresComment": True},
            {"id": "mot_07", "name": "Correa de accesorios (serpentina)",      "requiresPhoto": False, "requiresComment": True},
            {"id": "mot_08", "name": "Filtro de aire",                         "requiresPhoto": True,  "requiresComment": False},
            {"id": "mot_09", "name": "Mangueras y cañerías (fugas visibles)",  "requiresPhoto": True,  "requiresComment": True},
            {"id": "mot_10", "name": "Batería (estado, bornes y corrosión)",   "requiresPhoto": True,  "requiresComment": True},
            {"id": "mot_11", "name": "Alternador (carga correcta)",            "requiresPhoto": False, "requiresComment": True},
            {"id": "mot_12", "name": "Compresor de aire acondicionado",        "requiresPhoto": False, "requiresComment": True},
            {"id": "mot_13", "name": "Turbocompresor (si aplica)",             "requiresPhoto": False, "requiresComment": True, "defaultStatus": "na"},
            {"id": "mot_14", "name": "Intercooler (si aplica)",                "requiresPhoto": False, "requiresComment": True, "defaultStatus": "na"},
            {"id": "mot_15", "name": "Bujías / inyectores",                   "requiresPhoto": False, "requiresComment": True},
            {"id": "mot_16", "name": "Bomba de combustible",                   "requiresPhoto": False, "requiresComment": True},
            {"id": "mot_17", "name": "Estado general del compartimiento motor","requiresPhoto": True,  "requiresComment": True},
            {"id": "mot_18", "name": "Color y cantidad de humos del escape",   "requiresPhoto": False, "requiresComment": True},
        ],
    },
    {
        "id": "transmision",
        "name": "Transmisión",
        "order": 4,
        "icon": "car_repair",
        "items": [
            {"id": "tra_01", "name": "Embrague (presión, agarre y punto de entrega)",  "requiresPhoto": False, "requiresComment": True, "defaultStatus": "na"},
            {"id": "tra_02", "name": "Caja de cambios manual (sin ruidos ni golpes)",  "requiresPhoto": False, "requiresComment": True, "defaultStatus": "na"},
            {"id": "tra_03", "name": "Palier / semieje delantero izquierdo",           "requiresPhoto": False, "requiresComment": True},
            {"id": "tra_04", "name": "Palier / semieje delantero derecho",             "requiresPhoto": False, "requiresComment": True},
            {"id": "tra_05", "name": "Junta homocinética (trepidación al girar)",      "requiresPhoto": False, "requiresComment": True},
            {"id": "tra_06", "name": "Cardán / árbol de transmisión (4x4)",            "requiresPhoto": False, "requiresComment": True, "defaultStatus": "na"},
            {"id": "tra_07", "name": "Diferencial trasero",                            "requiresPhoto": False, "requiresComment": True, "defaultStatus": "na"},
            {"id": "tra_08", "name": "Fugas de aceite de transmisión",                 "requiresPhoto": True,  "requiresComment": True},
        ],
    },
    {
        "id": "caja_automatica",
        "name": "Caja Automática",
        "order": 5,
        "icon": "compare_arrows",
        "items": [
            {"id": "caj_01", "name": "Nivel y calidad del ATF (aceite de caja)",     "requiresPhoto": False, "requiresComment": True},
            {"id": "caj_02", "name": "Funcionamiento de marchas (P-R-N-D)",          "requiresPhoto": False, "requiresComment": True},
            {"id": "caj_03", "name": "Sin golpes al cambiar de marcha",              "requiresPhoto": False, "requiresComment": True},
            {"id": "caj_04", "name": "Punto de agarre del convertidor de par",       "requiresPhoto": False, "requiresComment": True},
            {"id": "caj_05", "name": "Funcionamiento modo Sport / Manual (si aplica)","requiresPhoto": False,"requiresComment": True, "defaultStatus": "na"},
            {"id": "caj_06", "name": "Fugas de ATF visibles",                        "requiresPhoto": True,  "requiresComment": True},
        ],
    },
    {
        "id": "suspension_delantera",
        "name": "Suspensión Delantera",
        "order": 6,
        "icon": "directions_car",
        "items": [
            {"id": "sud_01", "name": "Amortiguador delantero izquierdo",       "requiresPhoto": False, "requiresComment": True},
            {"id": "sud_02", "name": "Amortiguador delantero derecho",         "requiresPhoto": False, "requiresComment": True},
            {"id": "sud_03", "name": "Resorte delantero izquierdo",            "requiresPhoto": False, "requiresComment": True},
            {"id": "sud_04", "name": "Resorte delantero derecho",              "requiresPhoto": False, "requiresComment": True},
            {"id": "sud_05", "name": "Rótula inferior / superior",             "requiresPhoto": False, "requiresComment": True},
            {"id": "sud_06", "name": "Bujes de brazos delanteros",             "requiresPhoto": False, "requiresComment": True},
            {"id": "sud_07", "name": "Barra estabilizadora delantera",         "requiresPhoto": False, "requiresComment": True},
            {"id": "sud_08", "name": "Bujes de estabilizadora delantera",      "requiresPhoto": False, "requiresComment": True},
        ],
    },
    {
        "id": "suspension_trasera",
        "name": "Suspensión Trasera",
        "order": 7,
        "icon": "directions_car",
        "items": [
            {"id": "sut_01", "name": "Amortiguador trasero izquierdo",         "requiresPhoto": False, "requiresComment": True},
            {"id": "sut_02", "name": "Amortiguador trasero derecho",           "requiresPhoto": False, "requiresComment": True},
            {"id": "sut_03", "name": "Resorte trasero / ballesta",             "requiresPhoto": False, "requiresComment": True},
            {"id": "sut_04", "name": "Brazos traseros / tirador",              "requiresPhoto": False, "requiresComment": True},
            {"id": "sut_05", "name": "Bujes de brazos traseros",               "requiresPhoto": False, "requiresComment": True},
            {"id": "sut_06", "name": "Barra estabilizadora trasera",           "requiresPhoto": False, "requiresComment": True},
        ],
    },
    {
        "id": "direccion",
        "name": "Dirección",
        "order": 8,
        "icon": "radio_button_unchecked",
        "items": [
            {"id": "dir_01", "name": "Caja de dirección (juego excesivo)",     "requiresPhoto": False, "requiresComment": True},
            {"id": "dir_02", "name": "Cremallera de dirección",                "requiresPhoto": False, "requiresComment": True},
            {"id": "dir_03", "name": "Columna de dirección (telescópica)",     "requiresPhoto": False, "requiresComment": True},
            {"id": "dir_04", "name": "Bomba hidráulica / EPS eléctrico",       "requiresPhoto": False, "requiresComment": True},
            {"id": "dir_05", "name": "Biela de dirección izquierda",           "requiresPhoto": False, "requiresComment": True},
            {"id": "dir_06", "name": "Biela de dirección derecha",             "requiresPhoto": False, "requiresComment": True},
            {"id": "dir_07", "name": "Alineación (juego en volante en línea)", "requiresPhoto": False, "requiresComment": True},
            {"id": "dir_08", "name": "Desgaste irregular por convergencia",    "requiresPhoto": True,  "requiresComment": True},
        ],
    },
    {
        "id": "frenos_delanteros",
        "name": "Frenos Delanteros",
        "order": 9,
        "icon": "disc_full",
        "items": [
            {"id": "frd_01", "name": "Disco de freno delantero izquierdo",     "requiresPhoto": True,  "requiresComment": True},
            {"id": "frd_02", "name": "Disco de freno delantero derecho",       "requiresPhoto": True,  "requiresComment": True},
            {"id": "frd_03", "name": "Pastillas delanteras izquierdas (espesor)","requiresPhoto": False,"requiresComment": True},
            {"id": "frd_04", "name": "Pastillas delanteras derechas (espesor)","requiresPhoto": False, "requiresComment": True},
            {"id": "frd_05", "name": "Pinza de freno delantera izquierda",     "requiresPhoto": False, "requiresComment": True},
            {"id": "frd_06", "name": "Pinza de freno delantera derecha",       "requiresPhoto": False, "requiresComment": True},
            {"id": "frd_07", "name": "Mangueras y líneas de freno delanteras", "requiresPhoto": False, "requiresComment": True},
        ],
    },
    {
        "id": "frenos_traseros",
        "name": "Frenos Traseros",
        "order": 10,
        "icon": "disc_full",
        "items": [
            {"id": "frt_01", "name": "Disco/tambor trasero izquierdo",         "requiresPhoto": True,  "requiresComment": True},
            {"id": "frt_02", "name": "Disco/tambor trasero derecho",           "requiresPhoto": True,  "requiresComment": True},
            {"id": "frt_03", "name": "Pastillas/zapatas traseras izquierdas",  "requiresPhoto": False, "requiresComment": True},
            {"id": "frt_04", "name": "Pastillas/zapatas traseras derechas",    "requiresPhoto": False, "requiresComment": True},
            {"id": "frt_05", "name": "Pinza trasera izquierda / cilindro",     "requiresPhoto": False, "requiresComment": True},
            {"id": "frt_06", "name": "Freno de estacionamiento (eficacia)",    "requiresPhoto": False, "requiresComment": True},
            {"id": "frt_07", "name": "Mangueras y líneas de freno traseras",   "requiresPhoto": False, "requiresComment": True},
        ],
    },
    {
        "id": "llantas",
        "name": "Llantas",
        "order": 11,
        "icon": "tire_repair",
        "items": [
            {"id": "lla_01", "name": "Llanta delantera izquierda (golpes/grietas)","requiresPhoto": True, "requiresComment": True},
            {"id": "lla_02", "name": "Llanta delantera derecha",                  "requiresPhoto": True, "requiresComment": True},
            {"id": "lla_03", "name": "Llanta trasera izquierda",                  "requiresPhoto": True, "requiresComment": True},
            {"id": "lla_04", "name": "Llanta trasera derecha",                    "requiresPhoto": True, "requiresComment": True},
            {"id": "lla_05", "name": "Llanta de repuesto",                        "requiresPhoto": False,"requiresComment": True},
            {"id": "lla_06", "name": "Tuercas y pernos de rueda",                 "requiresPhoto": False,"requiresComment": True},
            {"id": "lla_07", "name": "Tapacubos / tapa central",                  "requiresPhoto": False,"requiresComment": False},
            {"id": "lla_08", "name": "Homologación y medidas",                    "requiresPhoto": False,"requiresComment": True},
        ],
    },
    {
        "id": "neumaticos",
        "name": "Neumáticos",
        "order": 12,
        "icon": "tire_repair",
        "items": [
            {"id": "neu_01", "name": "Neumático delantero izquierdo (profundidad banda rodadura)","requiresPhoto": True, "requiresComment": True},
            {"id": "neu_02", "name": "Neumático delantero derecho (profundidad)",  "requiresPhoto": True, "requiresComment": True},
            {"id": "neu_03", "name": "Neumático trasero izquierdo (profundidad)",  "requiresPhoto": True, "requiresComment": True},
            {"id": "neu_04", "name": "Neumático trasero derecho (profundidad)",    "requiresPhoto": True, "requiresComment": True},
            {"id": "neu_05", "name": "Desgaste homogéneo (sin desgaste irregular)","requiresPhoto": False,"requiresComment": True},
            {"id": "neu_06", "name": "Neumático de repuesto (presión y estado)",   "requiresPhoto": False,"requiresComment": True},
            {"id": "neu_07", "name": "Marca y medida homogénea en todos los ejes", "requiresPhoto": False,"requiresComment": False},
            {"id": "neu_08", "name": "Presión de inflado correcta",                "requiresPhoto": False,"requiresComment": True},
        ],
    },
    {
        "id": "electrico",
        "name": "Sistema Eléctrico",
        "order": 13,
        "icon": "electric_bolt",
        "items": [
            {"id": "ele_01", "name": "Luces delanteras cortas (low beam)",      "requiresPhoto": False, "requiresComment": True},
            {"id": "ele_02", "name": "Luces delanteras largas (high beam)",     "requiresPhoto": False, "requiresComment": True},
            {"id": "ele_03", "name": "Luces traseras y de freno",               "requiresPhoto": False, "requiresComment": True},
            {"id": "ele_04", "name": "Luces de posición (cuatro esquinas)",     "requiresPhoto": False, "requiresComment": True},
            {"id": "ele_05", "name": "Luces de niebla delantera / trasera",     "requiresPhoto": False, "requiresComment": True, "defaultStatus": "na"},
            {"id": "ele_06", "name": "Intermitentes / direccionales (todos)",   "requiresPhoto": False, "requiresComment": True},
            {"id": "ele_07", "name": "Luz de reversa",                          "requiresPhoto": False, "requiresComment": True},
            {"id": "ele_08", "name": "Bocina / claxon",                         "requiresPhoto": False, "requiresComment": True},
            {"id": "ele_09", "name": "Limpiaparabrisas y líquido lavador",      "requiresPhoto": False, "requiresComment": True},
            {"id": "ele_10", "name": "Sistema de audio / pantalla táctil",      "requiresPhoto": False, "requiresComment": True},
            {"id": "ele_11", "name": "Vidrios eléctricos (todos)",              "requiresPhoto": False, "requiresComment": True, "defaultStatus": "na"},
            {"id": "ele_12", "name": "Espejos retrovisores eléctricos",         "requiresPhoto": False, "requiresComment": True, "defaultStatus": "na"},
        ],
    },
    {
        "id": "electronica",
        "name": "Electrónica / Computadora",
        "order": 14,
        "icon": "computer",
        "items": [
            {"id": "elc_01", "name": "Diagnóstico OBD2 (códigos de falla activos)",  "requiresPhoto": True, "requiresComment": True},
            {"id": "elc_02", "name": "Airbags (testigos sin activar / sin pendientes)","requiresPhoto":False,"requiresComment": True},
            {"id": "elc_03", "name": "Sistema ABS (testigo)",                         "requiresPhoto": False,"requiresComment": True},
            {"id": "elc_04", "name": "ESP / ESC / Control de tracción",               "requiresPhoto": False,"requiresComment": True},
            {"id": "elc_05", "name": "Sensores de estacionamiento",                   "requiresPhoto": False,"requiresComment": True, "defaultStatus": "na"},
            {"id": "elc_06", "name": "Cámara de reversa",                             "requiresPhoto": False,"requiresComment": True, "defaultStatus": "na"},
            {"id": "elc_07", "name": "Control de crucero",                            "requiresPhoto": False,"requiresComment": True, "defaultStatus": "na"},
            {"id": "elc_08", "name": "Llaves electrónicas / transponder",             "requiresPhoto": False,"requiresComment": True},
            {"id": "elc_09", "name": "Alarma / inmovilizador de fábrica",             "requiresPhoto": False,"requiresComment": True},
        ],
    },
    {
        "id": "prueba_ruta",
        "name": "Prueba de Ruta",
        "order": 15,
        "icon": "route",
        "items": [
            {"id": "rut_01", "name": "Arranque en frío y en caliente",             "requiresPhoto": False, "requiresComment": True},
            {"id": "rut_02", "name": "Marcha mínima estable (ralentí)",            "requiresPhoto": False, "requiresComment": True},
            {"id": "rut_03", "name": "Aceleración y respuesta del motor",          "requiresPhoto": False, "requiresComment": True},
            {"id": "rut_04", "name": "Cambios de marcha (caja automática y manual)","requiresPhoto": False,"requiresComment": True},
            {"id": "rut_05", "name": "Frenado en línea recta (sin desviación)",    "requiresPhoto": False, "requiresComment": True},
            {"id": "rut_06", "name": "Comportamiento en curva (sin subviraje/sobreviraje)","requiresPhoto": False,"requiresComment": True},
            {"id": "rut_07", "name": "Ruidos y vibraciones a velocidad constante", "requiresPhoto": False, "requiresComment": True},
            {"id": "rut_08", "name": "Ruidos anómalos durante la frenada",         "requiresPhoto": False, "requiresComment": True},
            {"id": "rut_09", "name": "Temperatura del motor (no sobrecalienta)",   "requiresPhoto": False, "requiresComment": True},
            {"id": "rut_10", "name": "Humo del escape bajo carga",                 "requiresPhoto": False, "requiresComment": True},
            {"id": "rut_11", "name": "Funcionamiento del aire acondicionado (frío/calor)","requiresPhoto": False,"requiresComment": True},
            {"id": "rut_12", "name": "Odómetro y velocímetro (lectura coherente)", "requiresPhoto": True,  "requiresComment": True},
        ],
    },
]


def count_items(sections: list[dict]) -> int:
    return sum(len(s["items"]) for s in sections)


def build_template(sections: list[dict]) -> dict:
    now = datetime.now(timezone.utc)
    return {
        "id": TEMPLATE_ID,
        "tenantId": SYSTEM_TENANT,
        "name": "Inspección Precompra — Plantilla Base",
        "description": "Plantilla oficial para inspecciones precompra de vehículos livianos. "
                       "Incluye 15 secciones y 152 puntos de verificación.",
        "version": "1.0.0",
        "isSystem": True,
        "isActive": True,
        "totalItems": count_items(sections),
        "totalSections": len(sections),
        "sections": sections,
        "createdAt": now,
        "updatedAt": now,
        "createdBy": "seed_script",
        "updatedBy": "seed_script",
    }


def seed_template(db: firestore.Client, dry_run: bool = False) -> None:
    template = build_template(SECTIONS)
    total_items = template["totalItems"]

    table = Table(title=f"Plantilla Base — {total_items} puntos de inspección")
    table.add_column("#", style="cyan", width=4)
    table.add_column("Sección")
    table.add_column("Ítems", justify="right")

    for section in SECTIONS:
        table.add_row(
            str(section["order"]),
            section["name"],
            str(len(section["items"])),
        )

    console.print(table)
    console.print(f"\n[bold]Total secciones:[/bold] {len(SECTIONS)}")
    console.print(f"[bold]Total ítems:[/bold] {total_items}")

    if not dry_run:
        db.collection("inspection_templates").document(TEMPLATE_ID).set(template)
        console.print(f"\n[green]✓ Plantilla creada: inspection_templates/{TEMPLATE_ID}[/green]")
    else:
        console.print("\n[yellow]DRY RUN — plantilla no escrita[/yellow]")


@click.command()
@click.option("--project", default="taller-85514", help="Firebase Project ID")
@click.option("--dry-run", is_flag=True, help="Mostrar sin escribir en Firestore")
def main(project: str, dry_run: bool) -> None:
    """Crea la plantilla base de inspección precompra en Firestore."""
    console.print(f"[bold]Proyecto:[/bold] {project}")
    if dry_run:
        console.print("[yellow]MODO DRY RUN — sin cambios en Firestore[/yellow]")

    db = init_firebase(project)
    seed_template(db, dry_run=dry_run)


if __name__ == "__main__":
    main()
