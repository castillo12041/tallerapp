from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from app.features.qr.domain.entities import (
    InspectionSummary,
    QrCodeResult,
    QrVerification,
)


class QrCodeResponse(BaseModel):
    token_id: str
    encoded_token: str
    verify_url: str
    qr_image_b64: str
    expires_at: datetime
    resource_id: str
    tenant_id: str

    @classmethod
    def from_domain(cls, result: QrCodeResult) -> "QrCodeResponse":
        return cls(
            token_id=result.token_id,
            encoded_token=result.encoded_token,
            verify_url=result.verify_url,
            qr_image_b64=result.qr_image_b64,
            expires_at=result.expires_at,
            resource_id=result.resource_id,
            tenant_id=result.tenant_id,
        )


class InspectionSummaryResponse(BaseModel):
    id: str
    number: str
    status: str
    score: float | None
    vehicle_plate: str
    vehicle_make: str
    vehicle_model: str
    vehicle_year: int | None
    completed_at: datetime | None

    @classmethod
    def from_domain(cls, summary: InspectionSummary) -> "InspectionSummaryResponse":
        return cls(
            id=summary.id,
            number=summary.number,
            status=summary.status,
            score=summary.score,
            vehicle_plate=summary.vehicle_plate,
            vehicle_make=summary.vehicle_make,
            vehicle_model=summary.vehicle_model,
            vehicle_year=summary.vehicle_year,
            completed_at=summary.completed_at,
        )


class QrVerificationResponse(BaseModel):
    valid: bool
    reason: str | None = None
    token_id: str | None = None
    inspection: InspectionSummaryResponse | None = None
    expires_at: datetime | None = None
    revoked: bool = False

    @classmethod
    def from_domain(cls, result: QrVerification) -> "QrVerificationResponse":
        return cls(
            valid=result.valid,
            reason=result.reason,
            token_id=result.token_id,
            inspection=(
                InspectionSummaryResponse.from_domain(result.inspection)
                if result.inspection else None
            ),
            expires_at=result.expires_at,
            revoked=result.revoked,
        )
