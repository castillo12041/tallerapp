from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.config import settings
from app.core.firebase import get_firestore
from app.dependencies.auth import get_current_user
from app.dependencies.permissions import require_permission
from app.features.inspections.infrastructure.inspection_repository import (
    InspectionRepository,
)
from app.features.inspections.infrastructure.item_repository import ItemRepository
from app.features.pdf.application.use_case import GenerateInspectionPdfUseCase
from app.features.pdf.infrastructure.jinja_renderer import JinjaHtmlRenderer
from app.features.pdf.infrastructure.storage_uploader import FirebaseStorageUploader
from app.features.pdf.infrastructure.weasyprint_generator import WeasyPrintPdfGenerator
from app.features.pdf.presentation.schemas import GeneratePdfRequest, ReportResponse
from app.schemas.auth import TokenPayload

router = APIRouter()


# ---------------------------------------------------------------------------
# Dependency factories — exportadas para allow app.dependency_overrides en tests
# ---------------------------------------------------------------------------


def _get_inspection_repo() -> InspectionRepository:
    return InspectionRepository(db=get_firestore())


def _get_item_repo() -> ItemRepository:
    return ItemRepository(db=get_firestore())


def _get_pdf_generator() -> WeasyPrintPdfGenerator:
    return WeasyPrintPdfGenerator(renderer=JinjaHtmlRenderer())


def _get_storage_uploader() -> FirebaseStorageUploader:
    return FirebaseStorageUploader(bucket_name=settings.FIREBASE_STORAGE_BUCKET)


def _get_generate_uc(
    inspection_repo: Annotated[InspectionRepository, Depends(_get_inspection_repo)],
    item_repo: Annotated[ItemRepository, Depends(_get_item_repo)],
    pdf_generator: Annotated[WeasyPrintPdfGenerator, Depends(_get_pdf_generator)],
    storage_uploader: Annotated[FirebaseStorageUploader, Depends(_get_storage_uploader)],
) -> GenerateInspectionPdfUseCase:
    return GenerateInspectionPdfUseCase(
        inspection_repo=inspection_repo,
        item_repo=item_repo,
        pdf_generator=pdf_generator,
        storage_uploader=storage_uploader,
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post(
    "/inspections/{inspection_id}",
    response_model=ReportResponse,
    status_code=201,
    summary="Generar PDF de inspección",
    description=(
        "Genera el informe PDF de una inspección con el branding del taller. "
        "Solo disponible para inspecciones en estado 'review' o 'completed'. "
        "El PDF se sube a Firebase Storage y la URL queda guardada en la inspección."
    ),
)
async def generate_inspection_pdf(
    inspection_id: str,
    body: GeneratePdfRequest,
    current_user: Annotated[TokenPayload, Depends(require_permission("inspections:complete"))],
    uc: Annotated[GenerateInspectionPdfUseCase, Depends(_get_generate_uc)],
) -> ReportResponse:
    if not current_user.has_tenant:
        from app.core.exceptions import ForbiddenException
        raise ForbiddenException("Se requiere un tenant activo")

    report = await uc.execute(
        tenant_id=current_user.tenant_id,  # type: ignore[arg-type]
        inspection_id=inspection_id,
        branding=body.branding.to_domain(),
        generated_by=current_user.sub,
        qr_code_b64=body.qr_code_b64,
    )
    return ReportResponse.from_domain(report)
