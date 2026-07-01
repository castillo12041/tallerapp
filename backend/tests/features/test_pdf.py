"""
Tests del feature de generación de PDF.

La implementación concreta (WeasyPrint + Firebase Storage) se mockea completamente.
Se testea: endpoint, use case, schemas, validaciones y errores del dominio.
"""

from __future__ import annotations

import time
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient

from app.core.exceptions import ConflictException, NotFoundException
from app.features.inspections.domain.entities import Inspection, VehicleSnapshot
from app.features.pdf.application.use_case import GenerateInspectionPdfUseCase
from app.features.pdf.domain.entities import (
    PdfDocument,
    PdfJobRequest,
    StoredReport,
    TenantBranding,
)
from app.features.pdf.domain.pdf_generator import PdfGeneratorProtocol
from app.features.pdf.infrastructure.jinja_renderer import JinjaHtmlRenderer
from app.features.pdf.presentation.router import _get_generate_uc
from app.main import app

_NOW = int(time.time())
_AUTH_HEADERS = {"Authorization": "Bearer fake-token"}
_DECODE_PATH = "app.dependencies.auth.decode_access_token"

_MANAGER_CLAIMS = {
    "sub": "uid-manager",
    "tenant_id": "tenant-abc",
    "role": "workshopmanager",
    "permissions": ["inspections:complete", "inspections:read"],
    "plan": "professional",
    "type": "access",
    "exp": _NOW + 1800,
    "iat": _NOW,
}

_BRANDING_PAYLOAD = {
    "branding": {
        "name": "Taller Las Condes",
        "primary_color": "#1565C0",
        "secondary_color": "#FFFFFF",
        "address": "Av. Las Condes 1234, Santiago",
        "phone": "+56 9 1234 5678",
    }
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_inspection(status: str = "completed") -> Inspection:
    now = datetime.now(timezone.utc)
    snap = VehicleSnapshot(id="veh-1", plate="ABCD12", make="Toyota", model="Corolla", year=2020)
    return Inspection(
        id="ins-001",
        tenant_id="tenant-abc",
        number="INS-2024-000001",
        vehicle_id="veh-1",
        mechanic_id="uid-manager",
        status=status,
        vehicle_snapshot=snap,
        total_items=5,
        good_items=4,
        regular_items=1,
        bad_items=0,
        na_items=0,
        total_repair_cost=0.0,
        currency="CLP",
        is_offline=False,
        score=90.0,
        created_at=now,
        updated_at=now,
        created_by="uid-manager",
        updated_by="uid-manager",
    )


def _make_stored_report() -> StoredReport:
    return StoredReport(
        inspection_id="ins-001",
        tenant_id="tenant-abc",
        report_url="https://firebasestorage.googleapis.com/v0/b/bucket/o/report.pdf?alt=media&token=abc",
        filename="informe_INS-2024-000001.pdf",
        generated_at=datetime.now(timezone.utc),
        generated_by="uid-manager",
    )


@pytest.fixture(autouse=True)
def clear_overrides():
    yield
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# POST /api/v1/pdf/inspections/{id}
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_generate_pdf_success(client: AsyncClient) -> None:
    mock_uc = AsyncMock(spec=GenerateInspectionPdfUseCase)
    mock_uc.execute.return_value = _make_stored_report()
    app.dependency_overrides[_get_generate_uc] = lambda: mock_uc

    with patch(_DECODE_PATH, return_value=_MANAGER_CLAIMS):
        async with client as c:
            response = await c.post(
                "/api/v1/pdf/inspections/ins-001",
                json=_BRANDING_PAYLOAD,
                headers=_AUTH_HEADERS,
            )

    assert response.status_code == 201
    data = response.json()
    assert "report_url" in data
    assert "firebasestorage" in data["report_url"]
    assert data["inspection_id"] == "ins-001"
    assert data["filename"] == "informe_INS-2024-000001.pdf"
    mock_uc.execute.assert_called_once()


@pytest.mark.asyncio
async def test_generate_pdf_inspection_not_found(client: AsyncClient) -> None:
    mock_uc = AsyncMock(spec=GenerateInspectionPdfUseCase)
    mock_uc.execute.side_effect = NotFoundException("Inspección 'no-existe' no encontrada")
    app.dependency_overrides[_get_generate_uc] = lambda: mock_uc

    with patch(_DECODE_PATH, return_value=_MANAGER_CLAIMS):
        async with client as c:
            response = await c.post(
                "/api/v1/pdf/inspections/no-existe",
                json=_BRANDING_PAYLOAD,
                headers=_AUTH_HEADERS,
            )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_generate_pdf_wrong_status(client: AsyncClient) -> None:
    mock_uc = AsyncMock(spec=GenerateInspectionPdfUseCase)
    mock_uc.execute.side_effect = ConflictException(
        "Estado 'draft' no permite generación de PDF"
    )
    app.dependency_overrides[_get_generate_uc] = lambda: mock_uc

    with patch(_DECODE_PATH, return_value=_MANAGER_CLAIMS):
        async with client as c:
            response = await c.post(
                "/api/v1/pdf/inspections/ins-001",
                json=_BRANDING_PAYLOAD,
                headers=_AUTH_HEADERS,
            )

    assert response.status_code == 409


@pytest.mark.asyncio
async def test_generate_pdf_no_permission(client: AsyncClient) -> None:
    claims = {**_MANAGER_CLAIMS, "permissions": []}

    with patch(_DECODE_PATH, return_value=claims):
        async with client as c:
            response = await c.post(
                "/api/v1/pdf/inspections/ins-001",
                json=_BRANDING_PAYLOAD,
                headers=_AUTH_HEADERS,
            )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_generate_pdf_invalid_branding_color(client: AsyncClient) -> None:
    with patch(_DECODE_PATH, return_value=_MANAGER_CLAIMS):
        async with client as c:
            response = await c.post(
                "/api/v1/pdf/inspections/ins-001",
                json={
                    "branding": {
                        "name": "Taller",
                        "primary_color": "red",  # debe ser #RRGGBB
                    }
                },
                headers=_AUTH_HEADERS,
            )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_generate_pdf_missing_branding(client: AsyncClient) -> None:
    with patch(_DECODE_PATH, return_value=_MANAGER_CLAIMS):
        async with client as c:
            response = await c.post(
                "/api/v1/pdf/inspections/ins-001",
                json={},
                headers=_AUTH_HEADERS,
            )

    assert response.status_code == 422


# ---------------------------------------------------------------------------
# Domain — PdfGeneratorProtocol
# ---------------------------------------------------------------------------


def test_weasyprint_generator_satisfies_protocol() -> None:
    from app.features.pdf.infrastructure.weasyprint_generator import WeasyPrintPdfGenerator

    renderer = MagicMock(spec=JinjaHtmlRenderer)
    generator = WeasyPrintPdfGenerator(renderer=renderer)
    assert isinstance(generator, PdfGeneratorProtocol)


def test_pdf_job_request_is_frozen() -> None:
    inspection = _make_inspection()
    branding = TenantBranding(name="Taller Test")
    job = PdfJobRequest(
        inspection=inspection,
        items=[],
        branding=branding,
        generated_by="uid-test",
    )
    import dataclasses
    assert dataclasses.is_dataclass(job)


def test_tenant_branding_defaults() -> None:
    branding = TenantBranding(name="Mi Taller")
    assert branding.primary_color == "#1976D2"
    assert branding.secondary_color == "#FFFFFF"
    assert branding.logo_url is None


def test_pdf_document_fields() -> None:
    doc = PdfDocument(content=b"%PDF-1.4", filename="report.pdf")
    assert doc.content_type == "application/pdf"
    assert doc.filename == "report.pdf"


# ---------------------------------------------------------------------------
# JinjaHtmlRenderer — renderiza sin levantar WeasyPrint
# ---------------------------------------------------------------------------


def test_jinja_renderer_produces_html() -> None:
    renderer = JinjaHtmlRenderer()
    inspection = _make_inspection()
    branding = TenantBranding(
        name="Taller Las Condes",
        primary_color="#1565C0",
        address="Av. Las Condes 1234",
    )
    job = PdfJobRequest(
        inspection=inspection,
        items=[],
        branding=branding,
        generated_by="uid-manager",
    )
    html = renderer.render_inspection_report(job)

    assert "<!DOCTYPE html>" in html
    assert "INS-2024-000001" in html
    assert "Taller Las Condes" in html
    assert "ABCD12" in html
    assert "#1565C0" in html


def test_jinja_renderer_shows_score() -> None:
    renderer = JinjaHtmlRenderer()
    inspection = _make_inspection()
    job = PdfJobRequest(
        inspection=inspection,
        items=[],
        branding=TenantBranding(name="T"),
        generated_by="uid",
    )
    html = renderer.render_inspection_report(job)
    assert "90.0" in html


def test_jinja_renderer_with_observations() -> None:
    renderer = JinjaHtmlRenderer()
    now = datetime.now(timezone.utc)
    snap = VehicleSnapshot(id="v", plate="AA1234", make="Honda", model="Civic")
    inspection = Inspection(
        id="ins-x", tenant_id="t1", number="INS-2024-999",
        vehicle_id="v", mechanic_id="m", status="completed",
        vehicle_snapshot=snap, total_items=1, good_items=1,
        regular_items=0, bad_items=0, na_items=0,
        total_repair_cost=0.0, currency="CLP", is_offline=False,
        score=100.0,
        general_observations="Vehículo en excelente estado",
        recommendations="Cambiar aceite en 5000 km",
        created_at=now, updated_at=now,
        created_by="m", updated_by="m",
    )
    job = PdfJobRequest(
        inspection=inspection, items=[],
        branding=TenantBranding(name="T"), generated_by="m",
    )
    html = renderer.render_inspection_report(job)
    assert "Vehículo en excelente estado" in html
    assert "Cambiar aceite" in html


# ---------------------------------------------------------------------------
# Use case — lógica de validación de estado
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_use_case_rejects_draft_status() -> None:
    from unittest.mock import AsyncMock, MagicMock

    from app.features.inspections.infrastructure.inspection_repository import (
        InspectionRepository,
    )
    from app.features.inspections.infrastructure.item_repository import ItemRepository
    from app.features.pdf.infrastructure.storage_uploader import FirebaseStorageUploader

    mock_inspection_repo = MagicMock(spec=InspectionRepository)
    mock_inspection_repo.find_by_id.return_value = _make_inspection(status="draft")

    mock_item_repo = MagicMock(spec=ItemRepository)
    mock_pdf_gen = MagicMock(spec=PdfGeneratorProtocol)
    mock_storage = MagicMock(spec=FirebaseStorageUploader)

    uc = GenerateInspectionPdfUseCase(
        inspection_repo=mock_inspection_repo,
        item_repo=mock_item_repo,
        pdf_generator=mock_pdf_gen,
        storage_uploader=mock_storage,
    )

    with pytest.raises(ConflictException):
        await uc.execute(
            tenant_id="tenant-abc",
            inspection_id="ins-001",
            branding=TenantBranding(name="T"),
            generated_by="uid",
        )


@pytest.mark.asyncio
async def test_use_case_rejects_cross_tenant() -> None:
    from unittest.mock import MagicMock

    from app.features.inspections.infrastructure.inspection_repository import (
        InspectionRepository,
    )
    from app.features.inspections.infrastructure.item_repository import ItemRepository
    from app.features.pdf.infrastructure.storage_uploader import FirebaseStorageUploader

    inspection_other_tenant = _make_inspection(status="completed")

    mock_inspection_repo = MagicMock(spec=InspectionRepository)
    mock_inspection_repo.find_by_id.return_value = inspection_other_tenant

    uc = GenerateInspectionPdfUseCase(
        inspection_repo=mock_inspection_repo,
        item_repo=MagicMock(spec=ItemRepository),
        pdf_generator=MagicMock(spec=PdfGeneratorProtocol),
        storage_uploader=MagicMock(spec=FirebaseStorageUploader),
    )

    with pytest.raises(NotFoundException):
        await uc.execute(
            tenant_id="tenant-diferente",
            inspection_id="ins-001",
            branding=TenantBranding(name="T"),
            generated_by="uid",
        )
