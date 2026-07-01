from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from app.features.inspections.domain.entities import Inspection, InspectionItem


@dataclass(frozen=True)
class TenantBranding:
    name: str
    primary_color: str = "#1976D2"
    secondary_color: str = "#FFFFFF"
    logo_url: str | None = None
    address: str | None = None
    phone: str | None = None
    website: str | None = None
    footer_text: str | None = None


@dataclass(frozen=True)
class PdfJobRequest:
    inspection: Inspection
    items: list[InspectionItem]
    branding: TenantBranding
    generated_by: str
    qr_code_b64: str | None = None  # base64 PNG — si se pasa, se incrusta en el PDF


@dataclass(frozen=True)
class PdfDocument:
    content: bytes
    filename: str
    content_type: str = "application/pdf"


@dataclass(frozen=True)
class StoredReport:
    inspection_id: str
    tenant_id: str
    report_url: str
    filename: str
    generated_at: datetime
    generated_by: str
