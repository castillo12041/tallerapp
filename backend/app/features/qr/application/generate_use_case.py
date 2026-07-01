from __future__ import annotations

import uuid
from datetime import datetime, timezone, timedelta

from app.core.config import settings
from app.core.exceptions import ConflictException, NotFoundException
from app.core.utils import run_sync
from app.features.inspections.infrastructure.inspection_repository import (
    InspectionRepository,
)
from app.features.qr.domain.entities import PublicToken, QrCodeResult
from app.features.qr.infrastructure.hmac_signer import encode_token
from app.features.qr.infrastructure.public_token_repository import PublicTokenRepository
from app.features.qr.infrastructure.qr_code_generator import QrCodeGenerator

_ALLOWED_STATUSES = {"review", "completed"}
_TOKEN_TYPE = "qr_inspection"


class GenerateQrUseCase:
    def __init__(
        self,
        inspection_repo: InspectionRepository,
        token_repo: PublicTokenRepository,
        qr_generator: QrCodeGenerator,
    ) -> None:
        self._inspections = inspection_repo
        self._tokens = token_repo
        self._qr = qr_generator

    async def execute(
        self,
        tenant_id: str,
        resource_id: str,
        created_by: str,
    ) -> QrCodeResult:
        inspection = await run_sync(
            self._inspections.find_by_id, resource_id, tenant_id
        )
        if inspection is None or inspection.tenant_id != tenant_id:
            raise NotFoundException(f"Inspección '{resource_id}' no encontrada")

        if inspection.status not in _ALLOWED_STATUSES:
            raise ConflictException(
                f"Solo se puede generar QR de inspecciones en estado "
                f"{sorted(_ALLOWED_STATUSES)}. Estado actual: '{inspection.status}'"
            )

        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(days=settings.QR_TOKEN_EXPIRY_DAYS)
        token_id = str(uuid.uuid4())
        iat = int(now.timestamp())
        exp = int(expires_at.timestamp())

        encoded = encode_token(
            resource_id=resource_id,
            tenant_id=tenant_id,
            token_id=token_id,
            iat=iat,
            exp=exp,
            secret=settings.HMAC_SECRET_KEY,
        )

        verify_url = (
            f"{settings.PUBLIC_BASE_URL}{settings.API_V1_STR}"
            f"/qr/verify/{encoded}"
        )

        qr_image_b64 = await run_sync(self._qr.generate_b64, verify_url)

        token = PublicToken(
            id=token_id,
            tenant_id=tenant_id,
            resource_id=resource_id,
            token_type=_TOKEN_TYPE,
            issued_at=now,
            expires_at=expires_at,
            created_at=now,
            updated_at=now,
            created_by=created_by,
            updated_by=created_by,
        )
        await run_sync(self._tokens.create, token)

        return QrCodeResult(
            token_id=token_id,
            encoded_token=encoded,
            verify_url=verify_url,
            qr_image_b64=qr_image_b64,
            expires_at=expires_at,
            resource_id=resource_id,
            tenant_id=tenant_id,
        )
