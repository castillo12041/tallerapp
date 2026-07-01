from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass(frozen=True)
class PublicToken:
    """
    Token público almacenado en Firestore (colección `public_tokens`).
    Representa un QR de acceso a un informe de inspección.
    En Fase 11 también se usará para tokens de presupuesto (token_type='budget_access').
    """

    id: str               # UUID — usado como document ID y como jti en el payload
    tenant_id: str
    resource_id: str      # inspection_id para qr_inspection; estimate_id para budget_access
    token_type: str       # "qr_inspection" | "budget_access"
    issued_at: datetime
    expires_at: datetime
    created_at: datetime
    updated_at: datetime
    created_by: str
    updated_by: str
    revoked_at: datetime | None = None

    @property
    def is_revoked(self) -> bool:
        return self.revoked_at is not None

    @property
    def is_expired(self) -> bool:
        return datetime.now(timezone.utc) > self.expires_at

    @property
    def is_valid(self) -> bool:
        return not self.is_revoked and not self.is_expired


@dataclass(frozen=True)
class QrCodeResult:
    """Respuesta completa de la generación de QR."""

    token_id: str
    encoded_token: str       # base64url JSON firmado
    verify_url: str          # URL completa a escanear
    qr_image_b64: str        # PNG base64 listo para incrustar en PDF o <img>
    expires_at: datetime
    resource_id: str         # ID del recurso asociado (inspección o presupuesto)
    tenant_id: str


@dataclass(frozen=True)
class InspectionSummary:
    """Resumen mínimo de la inspección para mostrar en la verificación pública."""

    id: str
    number: str
    status: str
    score: float | None
    vehicle_plate: str
    vehicle_make: str
    vehicle_model: str
    vehicle_year: int | None
    completed_at: datetime | None


@dataclass(frozen=True)
class QrVerification:
    """Resultado de verificar un token QR (endpoint público)."""

    valid: bool
    reason: str | None = None
    token_id: str | None = None
    inspection: InspectionSummary | None = None
    expires_at: datetime | None = None
    revoked: bool = False
