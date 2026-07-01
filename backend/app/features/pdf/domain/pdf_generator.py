from __future__ import annotations

from typing import Protocol, runtime_checkable

from app.features.pdf.domain.entities import PdfDocument, PdfJobRequest


@runtime_checkable
class PdfGeneratorProtocol(Protocol):
    """
    Interfaz desacoplada para generación de PDFs.

    Permite intercambiar la implementación concreta (WeasyPrint, fpdf2, servicio externo)
    sin modificar la lógica de negocio. En Fase 19, esta interfaz permite extraer el
    generador a un microservicio `pdf_service/` independiente.
    """

    def generate(self, request: PdfJobRequest) -> PdfDocument:
        """Genera un PDF a partir del request y retorna el documento en bytes."""
        ...
