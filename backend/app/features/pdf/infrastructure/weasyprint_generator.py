from __future__ import annotations

from app.features.pdf.domain.entities import PdfDocument, PdfJobRequest
from app.features.pdf.infrastructure.jinja_renderer import JinjaHtmlRenderer


class WeasyPrintPdfGenerator:
    """
    Implementación concreta de PdfGeneratorProtocol usando WeasyPrint.

    WeasyPrint convierte HTML+CSS a PDF de alta calidad.
    Requiere librerías del sistema (Cairo, Pango, GLib) en producción Linux.
    En desarrollo Windows, la importación es lazy para no bloquear el arranque.

    Instalar: pip install weasyprint  (o pip install tallerapp-backend[pdf])
    """

    def __init__(self, renderer: JinjaHtmlRenderer) -> None:
        self._renderer = renderer

    def generate(self, request: PdfJobRequest) -> PdfDocument:
        html_content = self._renderer.render_inspection_report(request)
        pdf_bytes = self._render_to_pdf(html_content)
        filename = f"informe_{request.inspection.number}.pdf"
        return PdfDocument(content=pdf_bytes, filename=filename)

    @staticmethod
    def _render_to_pdf(html_content: str) -> bytes:
        try:
            from weasyprint import HTML  # lazy import — falla en Windows sin GTK
        except ImportError as exc:
            raise RuntimeError(
                "WeasyPrint no está instalado. "
                "Ejecutar: pip install 'tallerapp-backend[pdf]'. "
                "En Linux también se requiere: apt-get install libpango-1.0-0 libcairo2"
            ) from exc
        return HTML(string=html_content).write_pdf()  # type: ignore[no-any-return]
