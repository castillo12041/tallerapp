from __future__ import annotations

from datetime import datetime, timezone

from app.core.config import settings
from app.core.utils import run_sync
from app.features.inspections.infrastructure.inspection_repository import (
    InspectionRepository,
)
from app.features.qr.domain.entities import InspectionSummary, QrVerification
from app.features.qr.infrastructure.hmac_signer import decode_and_verify_token
from app.features.qr.infrastructure.public_token_repository import PublicTokenRepository


class VerifyQrUseCase:
    def __init__(
        self,
        inspection_repo: InspectionRepository,
        token_repo: PublicTokenRepository,
    ) -> None:
        self._inspections = inspection_repo
        self._tokens = token_repo

    async def execute(self, raw_token: str) -> QrVerification:
        payload = decode_and_verify_token(raw_token, settings.HMAC_SECRET_KEY)
        if payload is None:
            return QrVerification(valid=False, reason="Token inválido")

        now_ts = int(datetime.now(timezone.utc).timestamp())
        if payload["exp"] < now_ts:
            return QrVerification(valid=False, reason="Token expirado")

        stored = await run_sync(self._tokens.find_by_id, payload["jti"])
        if stored is None:
            return QrVerification(valid=False, reason="Token no encontrado")

        if stored.is_revoked:
            return QrVerification(valid=False, reason="Token revocado", revoked=True)

        inspection = await run_sync(
            self._inspections.find_by_id,
            payload["iid"],
            payload["tid"],
        )
        if inspection is None or inspection.tenant_id != payload["tid"]:
            return QrVerification(valid=False, reason="Inspección no encontrada")

        summary = InspectionSummary(
            id=inspection.id,
            number=inspection.number,
            status=inspection.status,
            score=inspection.score,
            vehicle_plate=inspection.vehicle_snapshot.plate,
            vehicle_make=inspection.vehicle_snapshot.make,
            vehicle_model=inspection.vehicle_snapshot.model,
            vehicle_year=inspection.vehicle_snapshot.year,
            completed_at=inspection.completed_at,
        )

        return QrVerification(
            valid=True,
            token_id=payload["jti"],
            inspection=summary,
            expires_at=stored.expires_at,
            revoked=False,
        )
