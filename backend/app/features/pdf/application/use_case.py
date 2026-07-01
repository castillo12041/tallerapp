from __future__ import annotations

from datetime import datetime, timezone

from app.core.exceptions import ConflictException, NotFoundException
from app.core.utils import run_sync
from app.features.inspections.infrastructure.inspection_repository import (
    InspectionRepository,
)
from app.features.inspections.infrastructure.item_repository import ItemRepository
from app.features.pdf.domain.entities import (
    PdfJobRequest,
    StoredReport,
    TenantBranding,
)
from app.features.pdf.domain.pdf_generator import PdfGeneratorProtocol
from app.features.pdf.infrastructure.storage_uploader import FirebaseStorageUploader

_ALLOWED_STATUSES = {"review", "completed"}


class GenerateInspectionPdfUseCase:
    def __init__(
        self,
        inspection_repo: InspectionRepository,
        item_repo: ItemRepository,
        pdf_generator: PdfGeneratorProtocol,
        storage_uploader: FirebaseStorageUploader,
    ) -> None:
        self._inspection_repo = inspection_repo
        self._item_repo = item_repo
        self._pdf_generator = pdf_generator
        self._storage_uploader = storage_uploader

    async def execute(
        self,
        tenant_id: str,
        inspection_id: str,
        branding: TenantBranding,
        generated_by: str,
        qr_code_b64: str | None = None,
    ) -> StoredReport:
        inspection = await run_sync(
            self._inspection_repo.find_by_id, inspection_id, tenant_id
        )
        if inspection is None or inspection.tenant_id != tenant_id:
            raise NotFoundException(f"Inspección '{inspection_id}' no encontrada")

        if inspection.status not in _ALLOWED_STATUSES:
            raise ConflictException(
                f"Solo se puede generar PDF de inspecciones en estado "
                f"{sorted(_ALLOWED_STATUSES)}. Estado actual: '{inspection.status}'"
            )

        items = await run_sync(self._item_repo.list_by_inspection, inspection_id)

        job = PdfJobRequest(
            inspection=inspection,
            items=items,
            branding=branding,
            generated_by=generated_by,
            qr_code_b64=qr_code_b64,
        )
        doc = await run_sync(self._pdf_generator.generate, job)

        report_url = await run_sync(
            self._storage_uploader.upload, doc, tenant_id, inspection_id
        )

        await run_sync(
            self._inspection_repo.update,
            inspection_id,
            tenant_id,
            {"report_url": report_url},
            generated_by,
        )

        return StoredReport(
            inspection_id=inspection_id,
            tenant_id=tenant_id,
            report_url=report_url,
            filename=doc.filename,
            generated_at=datetime.now(timezone.utc),
            generated_by=generated_by,
        )
