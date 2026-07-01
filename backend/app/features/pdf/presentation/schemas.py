from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.features.pdf.domain.entities import StoredReport, TenantBranding


class BrandingRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    primary_color: str = Field(default="#1976D2", pattern=r"^#[0-9A-Fa-f]{6}$")
    secondary_color: str = Field(default="#FFFFFF", pattern=r"^#[0-9A-Fa-f]{6}$")
    logo_url: str | None = Field(default=None, max_length=500)
    address: str | None = Field(default=None, max_length=200)
    phone: str | None = Field(default=None, max_length=30)
    website: str | None = Field(default=None, max_length=200)
    footer_text: str | None = Field(default=None, max_length=500)

    def to_domain(self) -> TenantBranding:
        return TenantBranding(
            name=self.name,
            primary_color=self.primary_color,
            secondary_color=self.secondary_color,
            logo_url=self.logo_url,
            address=self.address,
            phone=self.phone,
            website=self.website,
            footer_text=self.footer_text,
        )


class GeneratePdfRequest(BaseModel):
    branding: BrandingRequest
    qr_code_b64: str | None = Field(
        default=None,
        description="Base64 PNG del QR de verificación (generado por POST /api/v1/qr/inspections/{id})",
    )


class ReportResponse(BaseModel):
    inspection_id: str
    tenant_id: str
    report_url: str
    filename: str
    generated_at: datetime
    generated_by: str

    @classmethod
    def from_domain(cls, report: StoredReport) -> "ReportResponse":
        return cls(
            inspection_id=report.inspection_id,
            tenant_id=report.tenant_id,
            report_url=report.report_url,
            filename=report.filename,
            generated_at=report.generated_at,
            generated_by=report.generated_by,
        )
