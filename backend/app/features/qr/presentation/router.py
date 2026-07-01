from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.firebase import get_firestore
from app.dependencies.permissions import require_permission
from app.features.inspections.infrastructure.inspection_repository import (
    InspectionRepository,
)
from app.features.qr.application.generate_use_case import GenerateQrUseCase
from app.features.qr.application.verify_use_case import VerifyQrUseCase
from app.features.qr.infrastructure.public_token_repository import PublicTokenRepository
from app.features.qr.infrastructure.qr_code_generator import QrCodeGenerator
from app.features.qr.presentation.schemas import QrCodeResponse, QrVerificationResponse
from app.core.exceptions import NotFoundException
from app.core.utils import run_sync
from app.schemas.auth import TokenPayload

router = APIRouter()


# ---------------------------------------------------------------------------
# Dependency factories — exportadas para app.dependency_overrides en tests
# ---------------------------------------------------------------------------


def _get_inspection_repo() -> InspectionRepository:
    return InspectionRepository(db=get_firestore())


def _get_token_repo() -> PublicTokenRepository:
    return PublicTokenRepository(db=get_firestore())


def _get_qr_generator() -> QrCodeGenerator:
    return QrCodeGenerator()


def _get_generate_uc(
    inspection_repo: Annotated[InspectionRepository, Depends(_get_inspection_repo)],
    token_repo: Annotated[PublicTokenRepository, Depends(_get_token_repo)],
    qr_generator: Annotated[QrCodeGenerator, Depends(_get_qr_generator)],
) -> GenerateQrUseCase:
    return GenerateQrUseCase(
        inspection_repo=inspection_repo,
        token_repo=token_repo,
        qr_generator=qr_generator,
    )


def _get_verify_uc(
    inspection_repo: Annotated[InspectionRepository, Depends(_get_inspection_repo)],
    token_repo: Annotated[PublicTokenRepository, Depends(_get_token_repo)],
) -> VerifyQrUseCase:
    return VerifyQrUseCase(
        inspection_repo=inspection_repo,
        token_repo=token_repo,
    )


# ---------------------------------------------------------------------------
# Endpoints autenticados
# ---------------------------------------------------------------------------


@router.post(
    "/inspections/{inspection_id}",
    response_model=QrCodeResponse,
    status_code=201,
    summary="Generar código QR de inspección",
    description=(
        "Genera un QR firmado HMAC-SHA256 que apunta a la URL de verificación pública. "
        "Solo disponible para inspecciones en estado 'review' o 'completed'. "
        "El token se almacena en la colección `public_tokens` para permitir revocación."
    ),
)
async def generate_qr(
    inspection_id: str,
    current_user: Annotated[TokenPayload, Depends(require_permission("inspections:complete"))],
    uc: Annotated[GenerateQrUseCase, Depends(_get_generate_uc)],
) -> QrCodeResponse:
    result = await uc.execute(
        tenant_id=current_user.tenant_id,  # type: ignore[arg-type]
        resource_id=inspection_id,
        created_by=current_user.sub,
    )
    return QrCodeResponse.from_domain(result)


@router.delete(
    "/tokens/{token_id}",
    status_code=204,
    summary="Revocar token QR",
    description="Revoca un token QR. El QR físico ya impreso dejará de ser válido.",
)
async def revoke_qr_token(
    token_id: str,
    current_user: Annotated[TokenPayload, Depends(require_permission("inspections:complete"))],
    token_repo: Annotated[PublicTokenRepository, Depends(_get_token_repo)],
) -> None:
    stored = await run_sync(token_repo.find_by_id, token_id)
    if stored is None or stored.tenant_id != current_user.tenant_id:
        raise NotFoundException(f"Token '{token_id}' no encontrado")
    await run_sync(token_repo.revoke, token_id, current_user.sub)


# ---------------------------------------------------------------------------
# Endpoint público (sin autenticación JWT)
# ---------------------------------------------------------------------------


@router.get(
    "/verify/{token}",
    response_model=QrVerificationResponse,
    summary="Verificar código QR (público)",
    description=(
        "Endpoint público — no requiere autenticación. "
        "Verifica la firma HMAC y el estado del token en Firestore. "
        "Retorna resumen de la inspección si el token es válido."
    ),
)
async def verify_qr(
    token: str,
    uc: Annotated[VerifyQrUseCase, Depends(_get_verify_uc)],
) -> QrVerificationResponse:
    result = await uc.execute(token)
    return QrVerificationResponse.from_domain(result)
