"""
Tests del feature de códigos QR.

La generación de imagen QR (qrcode/Pillow) y Firestore se mockean completamente.
Se testea: endpoints, HMAC signer, use cases, validaciones, revocación, verificación.
"""

from __future__ import annotations

import time
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient

from app.core.exceptions import ConflictException, NotFoundException
from app.features.inspections.domain.entities import Inspection, VehicleSnapshot
from app.features.qr.application.generate_use_case import GenerateQrUseCase
from app.features.qr.application.verify_use_case import VerifyQrUseCase
from app.features.qr.domain.entities import (
    InspectionSummary,
    PublicToken,
    QrCodeResult,
    QrVerification,
)
from app.features.qr.infrastructure.hmac_signer import (
    decode_and_verify_token,
    encode_token,
)
from app.features.qr.infrastructure.public_token_repository import PublicTokenRepository
from app.features.qr.infrastructure.qr_code_generator import QrCodeGenerator
from app.features.qr.presentation.router import _get_generate_uc, _get_verify_uc
from app.main import app

_NOW = int(time.time())
_AUTH_HEADERS = {"Authorization": "Bearer fake-token"}
_DECODE_PATH = "app.dependencies.auth.decode_access_token"
_SECRET = "test-hmac-secret-key-32-characters!!"

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


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_inspection(status: str = "completed") -> Inspection:
    now = datetime.now(timezone.utc)
    snap = VehicleSnapshot(
        id="veh-1", plate="ABCD12", make="Toyota", model="Corolla", year=2020
    )
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


def _make_qr_result() -> QrCodeResult:
    now = datetime.now(timezone.utc)
    return QrCodeResult(
        token_id="tok-uuid-001",
        encoded_token="eyJ0ZXN0IjoiZGF0YSJ9",
        verify_url="https://example.com/api/v1/qr/verify/eyJ0ZXN0IjoiZGF0YSJ9",
        qr_image_b64="iVBORw0KGgo=",
        expires_at=now + timedelta(days=365),
        resource_id="ins-001",
        tenant_id="tenant-abc",
    )


def _make_public_token(revoked: bool = False) -> PublicToken:
    now = datetime.now(timezone.utc)
    return PublicToken(
        id="tok-uuid-001",
        tenant_id="tenant-abc",
        resource_id="ins-001",
        token_type="qr_inspection",
        issued_at=now,
        expires_at=now + timedelta(days=365),
        created_at=now,
        updated_at=now,
        created_by="uid-manager",
        updated_by="uid-manager",
        revoked_at=now if revoked else None,
    )


@pytest.fixture(autouse=True)
def clear_overrides():
    yield
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# POST /api/v1/qr/inspections/{id}
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_generate_qr_success(client: AsyncClient) -> None:
    mock_uc = AsyncMock(spec=GenerateQrUseCase)
    mock_uc.execute.return_value = _make_qr_result()
    app.dependency_overrides[_get_generate_uc] = lambda: mock_uc

    with patch(_DECODE_PATH, return_value=_MANAGER_CLAIMS):
        async with client as c:
            response = await c.post(
                "/api/v1/qr/inspections/ins-001", headers=_AUTH_HEADERS
            )

    assert response.status_code == 201
    data = response.json()
    assert data["token_id"] == "tok-uuid-001"
    assert "verify_url" in data
    assert "qr_image_b64" in data
    assert data["resource_id"] == "ins-001"
    mock_uc.execute.assert_called_once_with(
        tenant_id="tenant-abc", resource_id="ins-001", created_by="uid-manager"
    )


@pytest.mark.asyncio
async def test_generate_qr_inspection_not_found(client: AsyncClient) -> None:
    mock_uc = AsyncMock(spec=GenerateQrUseCase)
    mock_uc.execute.side_effect = NotFoundException("no encontrada")
    app.dependency_overrides[_get_generate_uc] = lambda: mock_uc

    with patch(_DECODE_PATH, return_value=_MANAGER_CLAIMS):
        async with client as c:
            response = await c.post(
                "/api/v1/qr/inspections/no-existe", headers=_AUTH_HEADERS
            )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_generate_qr_wrong_status(client: AsyncClient) -> None:
    mock_uc = AsyncMock(spec=GenerateQrUseCase)
    mock_uc.execute.side_effect = ConflictException("Estado draft no permitido")
    app.dependency_overrides[_get_generate_uc] = lambda: mock_uc

    with patch(_DECODE_PATH, return_value=_MANAGER_CLAIMS):
        async with client as c:
            response = await c.post(
                "/api/v1/qr/inspections/ins-001", headers=_AUTH_HEADERS
            )

    assert response.status_code == 409


@pytest.mark.asyncio
async def test_generate_qr_no_permission(client: AsyncClient) -> None:
    claims = {**_MANAGER_CLAIMS, "permissions": []}

    with patch(_DECODE_PATH, return_value=claims):
        async with client as c:
            response = await c.post(
                "/api/v1/qr/inspections/ins-001", headers=_AUTH_HEADERS
            )

    assert response.status_code == 403


# ---------------------------------------------------------------------------
# GET /api/v1/qr/verify/{token} (público, sin auth)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_verify_qr_valid(client: AsyncClient) -> None:
    now = datetime.now(timezone.utc)
    summary = InspectionSummary(
        id="ins-001", number="INS-2024-000001", status="completed",
        score=90.0, vehicle_plate="ABCD12", vehicle_make="Toyota",
        vehicle_model="Corolla", vehicle_year=2020, completed_at=now,
    )
    mock_uc = AsyncMock(spec=VerifyQrUseCase)
    mock_uc.execute.return_value = QrVerification(
        valid=True, token_id="tok-001",
        inspection=summary,
        expires_at=now + timedelta(days=365),
        revoked=False,
    )
    app.dependency_overrides[_get_verify_uc] = lambda: mock_uc

    async with client as c:
        response = await c.get("/api/v1/qr/verify/some-encoded-token")

    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is True
    assert data["inspection"]["number"] == "INS-2024-000001"
    assert data["inspection"]["score"] == 90.0
    assert data["revoked"] is False


@pytest.mark.asyncio
async def test_verify_qr_invalid_token(client: AsyncClient) -> None:
    mock_uc = AsyncMock(spec=VerifyQrUseCase)
    mock_uc.execute.return_value = QrVerification(valid=False, reason="Token inválido")
    app.dependency_overrides[_get_verify_uc] = lambda: mock_uc

    async with client as c:
        response = await c.get("/api/v1/qr/verify/garbage-token")

    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is False
    assert data["reason"] == "Token inválido"


@pytest.mark.asyncio
async def test_verify_qr_revoked(client: AsyncClient) -> None:
    mock_uc = AsyncMock(spec=VerifyQrUseCase)
    mock_uc.execute.return_value = QrVerification(
        valid=False, reason="Token revocado", revoked=True
    )
    app.dependency_overrides[_get_verify_uc] = lambda: mock_uc

    async with client as c:
        response = await c.get("/api/v1/qr/verify/revoked-token")

    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is False
    assert data["revoked"] is True


@pytest.mark.asyncio
async def test_verify_qr_no_auth_required(client: AsyncClient) -> None:
    """El endpoint /qr/verify no requiere JWT."""
    mock_uc = AsyncMock(spec=VerifyQrUseCase)
    mock_uc.execute.return_value = QrVerification(valid=False, reason="Token inválido")
    app.dependency_overrides[_get_verify_uc] = lambda: mock_uc

    async with client as c:
        # Sin headers de autorización
        response = await c.get("/api/v1/qr/verify/some-token")

    assert response.status_code == 200  # 200, no 401


# ---------------------------------------------------------------------------
# DELETE /api/v1/qr/tokens/{token_id}
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_revoke_token_not_found(client: AsyncClient) -> None:
    from app.features.qr.presentation.router import _get_token_repo

    mock_repo = MagicMock(spec=PublicTokenRepository)
    mock_repo.find_by_id.return_value = None
    app.dependency_overrides[_get_token_repo] = lambda: mock_repo

    with patch(_DECODE_PATH, return_value=_MANAGER_CLAIMS):
        async with client as c:
            response = await c.delete(
                "/api/v1/qr/tokens/no-existe", headers=_AUTH_HEADERS
            )

    assert response.status_code == 404


# ---------------------------------------------------------------------------
# HMAC Signer — tests unitarios puros
# ---------------------------------------------------------------------------


def test_encode_decode_round_trip() -> None:
    token = encode_token(
        resource_id="ins-001",
        tenant_id="tenant-abc",
        token_id="tok-001",
        iat=1700000000,
        exp=1731536000,
        secret=_SECRET,
    )
    payload = decode_and_verify_token(token, _SECRET)
    assert payload is not None
    assert payload["iid"] == "ins-001"
    assert payload["tid"] == "tenant-abc"
    assert payload["jti"] == "tok-001"


def test_tampered_payload_rejected() -> None:
    token = encode_token(
        resource_id="ins-001",
        tenant_id="tenant-abc",
        token_id="tok-001",
        iat=1700000000,
        exp=1731536000,
        secret=_SECRET,
    )
    import base64, json
    padded = token + "=" * (4 - len(token) % 4)
    payload = json.loads(base64.urlsafe_b64decode(padded))
    payload["iid"] = "ins-999"  # tampering
    tampered_json = json.dumps(payload, separators=(",", ":")).encode()
    tampered_token = base64.urlsafe_b64encode(tampered_json).decode().rstrip("=")
    result = decode_and_verify_token(tampered_token, _SECRET)
    assert result is None


def test_wrong_secret_rejected() -> None:
    token = encode_token(
        resource_id="ins-001",
        tenant_id="tenant-abc",
        token_id="tok-001",
        iat=1700000000,
        exp=1731536000,
        secret=_SECRET,
    )
    result = decode_and_verify_token(token, "wrong-secret")
    assert result is None


def test_garbage_token_rejected() -> None:
    assert decode_and_verify_token("not-base64!!!", _SECRET) is None
    assert decode_and_verify_token("", _SECRET) is None


def test_missing_fields_rejected() -> None:
    import base64, json
    incomplete = json.dumps({"iid": "ins-001"}).encode()
    token = base64.urlsafe_b64encode(incomplete).decode().rstrip("=")
    assert decode_and_verify_token(token, _SECRET) is None


# ---------------------------------------------------------------------------
# PublicToken domain
# ---------------------------------------------------------------------------


def test_public_token_valid() -> None:
    token = _make_public_token(revoked=False)
    assert token.is_valid
    assert not token.is_revoked
    assert not token.is_expired


def test_public_token_revoked() -> None:
    token = _make_public_token(revoked=True)
    assert token.is_revoked
    assert not token.is_valid


def test_public_token_expired() -> None:
    now = datetime.now(timezone.utc)
    token = PublicToken(
        id="t", tenant_id="t", resource_id="i", token_type="qr_inspection",
        issued_at=now - timedelta(days=2),
        expires_at=now - timedelta(days=1),  # pasado
        created_at=now, updated_at=now, created_by="u", updated_by="u",
    )
    assert token.is_expired
    assert not token.is_valid


# ---------------------------------------------------------------------------
# Use case — validación de estado
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_generate_use_case_rejects_draft() -> None:
    from app.features.inspections.infrastructure.inspection_repository import (
        InspectionRepository,
    )

    mock_repo = MagicMock(spec=InspectionRepository)
    mock_repo.find_by_id.return_value = _make_inspection(status="draft")

    uc = GenerateQrUseCase(
        inspection_repo=mock_repo,
        token_repo=MagicMock(spec=PublicTokenRepository),
        qr_generator=MagicMock(spec=QrCodeGenerator),
    )

    with pytest.raises(ConflictException):
        await uc.execute(
            tenant_id="tenant-abc",
            resource_id="ins-001",
            created_by="uid",
        )


@pytest.mark.asyncio
async def test_generate_use_case_rejects_cross_tenant() -> None:
    from app.features.inspections.infrastructure.inspection_repository import (
        InspectionRepository,
    )

    mock_repo = MagicMock(spec=InspectionRepository)
    mock_repo.find_by_id.return_value = _make_inspection()  # tenant-abc

    uc = GenerateQrUseCase(
        inspection_repo=mock_repo,
        token_repo=MagicMock(spec=PublicTokenRepository),
        qr_generator=MagicMock(spec=QrCodeGenerator),
    )

    with pytest.raises(NotFoundException):
        await uc.execute(
            tenant_id="tenant-otro",
            resource_id="ins-001",
            created_by="uid",
        )
