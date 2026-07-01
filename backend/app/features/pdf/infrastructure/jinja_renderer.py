from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.features.inspections.domain.entities import InspectionItem
from app.features.pdf.domain.entities import PdfJobRequest

_TEMPLATES_DIR = Path(__file__).parent / "templates"

_STATUS_LABELS: dict[str, str] = {
    "good": "Bueno",
    "regular": "Regular",
    "bad": "Deficiente",
    "na": "N/A",
    "pending": "Pendiente",
}

_STATUS_COLORS: dict[str, str] = {
    "good": "#2e7d32",
    "regular": "#f57c00",
    "bad": "#c62828",
    "na": "#757575",
    "pending": "#9e9e9e",
}

_STATUS_BG: dict[str, str] = {
    "good": "#e8f5e9",
    "regular": "#fff3e0",
    "bad": "#ffebee",
    "na": "#f5f5f5",
    "pending": "#fafafa",
}


def _group_items_by_category(items: list[InspectionItem]) -> list[dict]:
    categories: dict[str, dict] = {}
    for item in sorted(items, key=lambda i: (i.category_order, i.order)):
        if item.category not in categories:
            categories[item.category] = {
                "name": item.category,
                "order": item.category_order,
                "items": [],
            }
        categories[item.category]["items"].append(item)
    return list(categories.values())


class JinjaHtmlRenderer:
    def __init__(self) -> None:
        self._env = Environment(
            loader=FileSystemLoader(str(_TEMPLATES_DIR)),
            autoescape=select_autoescape(["html"]),
        )

    def render_inspection_report(self, request: PdfJobRequest) -> str:
        template = self._env.get_template("inspection_report.html")
        inspection = request.inspection
        evaluated = (
            inspection.good_items
            + inspection.regular_items
            + inspection.bad_items
        )
        return template.render(
            inspection=inspection,
            branding=request.branding,
            categories=_group_items_by_category(request.items),
            status_labels=_STATUS_LABELS,
            status_colors=_STATUS_COLORS,
            status_bg=_STATUS_BG,
            evaluated_items=evaluated,
            qr_code_b64=request.qr_code_b64,
        )
