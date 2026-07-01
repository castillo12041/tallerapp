"""
Tests de la feature de autenticación.

Usa dependency overrides de FastAPI para aislar los casos de uso
de Firebase y Firestore — sin mocks de bajo nivel de infraestructura.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient

from app.core.exceptions import ForbiddenException, NotFoundException, UnauthorizedException
from app.features.auth.application.use_cases import LoginUseCase, LogoutUseCase, RefreshUseCase
from app.features.auth.domain.entities import AuthUser, UserRole
from app.features.auth.infrastructure.token_repository import RefreshTokenRecord
from app.features.auth.presentation.router import (
    _get_login_use_case,
    _get_logout_use_case,
    _get_refresh_use_case,
)
from app.main import app
from app.schemas.auth import TokenResponse
from tests.conftest import JWT_TEST_SECRET


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_token_response() -> TokenResponse:
    return TokenResponse(
        access_token="fake-access-token",
        refresh_token="fake-refresh-token",
        expires_in=1800,
    )


def _make_auth_user(*, is_active: bool = True, uid: str = "uid-test") -> AuthUser:
    return AuthUser(
        uid=uid,
        email="test@example.com",
        display_name="Test User",
        role=UserRole.INSPECTOR,
        permissions=["inspections:read"],
        tenant_id="tenant-abc",
        plan="professional",
        is_active=is_active,
    )


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def clear_overrides():
    yield
    app.dependency_overrides.clear()


def _override_login(use_case: LoginUseCase) -> None:
    app.dependency_overrides[_get_login_use_case] = lambda: use_case


def _override_refresh(use_case: RefreshUseCase) -> None:
    app.dependency_overrides[_get_refresh_use_case] = lambda: use_case


def _override_logout(use_case: LogoutUseCase) -> None:
    app.dependency_overrides[_get_logout_use_case] = lambda: use_case


# ---------------------------------------------------------------------------
# POST /auth/login
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient) -> None:
    mock_uc = AsyncMock(spec=LoginUseCase)
    mock_uc.execute.return_value = _make_token_response()
    _override_login(mock_uc)

    async with client as c:
        response = await c.post("/api/v1/auth/login", json={"id_token": "valid-firebase-token"})

    assert response.status_code == 200
    data = response.json()
    assert data["access_token"] == "fake-access-token"
    assert data["refresh_token"] == "fake-refresh-token"
    assert data["token_type"] == "Bearer"
    assert data["expires_in"] == 1800
    mock_uc.execute.assert_called_once_with("valid-firebase-token")


@pytest.mark.asyncio
async def test_login_invalid_firebase_token(client: AsyncClient) -> None:
    mock_uc = AsyncMock(spec=LoginUseCase)
    mock_uc.execute.side_effect = UnauthorizedException("Firebase ID Token inválido o expirado")
    _override_login(mock_uc)

    async with client as c:
        response = await c.post("/api/v1/auth/login", json={"id_token": "bad-token"})

    assert response.status_code == 401
    assert response.json()["error_code"] == "UNAUTHORIZED"


@pytest.mark.asyncio
async def test_login_user_not_found(client: AsyncClient) -> None:
    mock_uc = AsyncMock(spec=LoginUseCase)
    mock_uc.execute.side_effect = NotFoundException("Usuario no encontrado")
    _override_login(mock_uc)

    async with client as c:
        response = await c.post("/api/v1/auth/login", json={"id_token": "valid-token"})

    assert response.status_code == 404
    assert response.json()["error_code"] == "NOT_FOUND"


@pytest.mark.asyncio
async def test_login_inactive_user(client: AsyncClient) -> None:
    mock_uc = AsyncMock(spec=LoginUseCase)
    mock_uc.execute.side_effect = ForbiddenException("Cuenta desactivada")
    _override_login(mock_uc)

    async with client as c:
        response = await c.post("/api/v1/auth/login", json={"id_token": "valid-token"})

    assert response.status_code == 403
    assert response.json()["error_code"] == "FORBIDDEN"


@pytest.mark.asyncio
async def test_login_missing_id_token(client: AsyncClient) -> None:
    async with client as c:
        response = await c.post("/api/v1/auth/login", json={})
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# POST /auth/refresh
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_refresh_success(client: AsyncClient) -> None:
    mock_uc = AsyncMock(spec=RefreshUseCase)
    mock_uc.execute.return_value = _make_token_response()
    _override_refresh(mock_uc)

    async with client as c:
        response = await c.post("/api/v1/auth/refresh", json={"refresh_token": "old-refresh"})

    assert response.status_code == 200
    assert response.json()["access_token"] == "fake-access-token"
    mock_uc.execute.assert_called_once_with("old-refresh")


@pytest.mark.asyncio
async def test_refresh_expired_token(client: AsyncClient) -> None:
    mock_uc = AsyncMock(spec=RefreshUseCase)
    mock_uc.execute.side_effect = UnauthorizedException("Refresh token inválido o expirado.")
    _override_refresh(mock_uc)

    async with client as c:
        response = await c.post("/api/v1/auth/refresh", json={"refresh_token": "expired"})

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_refresh_token_reuse_detected(client: AsyncClient) -> None:
    mock_uc = AsyncMock(spec=RefreshUseCase)
    mock_uc.execute.side_effect = UnauthorizedException("Sesión comprometida.")
    _override_refresh(mock_uc)

    async with client as c:
        response = await c.post("/api/v1/auth/refresh", json={"refresh_token": "reused-token"})

    assert response.status_code == 401
    assert "error_code" in response.json()


# ---------------------------------------------------------------------------
# POST /auth/logout
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_logout_success(client: AsyncClient) -> None:
    mock_uc = AsyncMock(spec=LogoutUseCase)
    mock_uc.execute.return_value = None
    _override_logout(mock_uc)

    async with client as c:
        response = await c.post("/api/v1/auth/logout", json={"refresh_token": "some-token"})

    assert response.status_code == 204
    mock_uc.execute.assert_called_once_with("some-token")


@pytest.mark.asyncio
async def test_logout_missing_body(client: AsyncClient) -> None:
    async with client as c:
        response = await c.post("/api/v1/auth/logout", json={})
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# GET /auth/me
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_me_without_token(client: AsyncClient) -> None:
    async with client as c:
        response = await c.get("/api/v1/auth/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_me_with_valid_token(client: AsyncClient) -> None:
    with patch("app.core.security.settings") as mock_settings:
        mock_settings.JWT_SECRET_KEY = JWT_TEST_SECRET
        mock_settings.JWT_ALGORITHM = "HS256"
        mock_settings.ACCESS_TOKEN_EXPIRE_MINUTES = 30

        from app.core.security import create_access_token

        token = create_access_token(
            subject="uid-test-123",
            tenant_id="tenant-abc",
            role="inspector",
            permissions=["inspections:read"],
            plan="professional",
        )

        async with client as c:
            response = await c.get(
                "/api/v1/auth/me",
                headers={"Authorization": f"Bearer {token}"},
            )

    assert response.status_code == 200
    data = response.json()
    assert data["sub"] == "uid-test-123"
    assert data["role"] == "inspector"
    assert data["tenant_id"] == "tenant-abc"


# ---------------------------------------------------------------------------
# LoginUseCase — tests unitarios del dominio
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_login_use_case_user_not_found() -> None:
    mock_user_repo = MagicMock()
    mock_user_repo.find_by_uid.return_value = None

    with patch(
        "app.features.auth.application.use_cases.verify_firebase_id_token",
        return_value={"uid": "uid-test"},
    ):
        use_case = LoginUseCase(user_repo=mock_user_repo, token_repo=MagicMock())
        with pytest.raises(NotFoundException):
            await use_case.execute("fake-firebase-token")


@pytest.mark.asyncio
async def test_login_use_case_inactive_user() -> None:
    mock_user_repo = MagicMock()
    mock_user_repo.find_by_uid.return_value = _make_auth_user(is_active=False)

    with patch(
        "app.features.auth.application.use_cases.verify_firebase_id_token",
        return_value={"uid": "uid-test"},
    ):
        use_case = LoginUseCase(user_repo=mock_user_repo, token_repo=MagicMock())
        with pytest.raises(ForbiddenException):
            await use_case.execute("fake-token")


# ---------------------------------------------------------------------------
# RefreshTokenRecord — tests unitarios del dominio
# ---------------------------------------------------------------------------


def test_refresh_token_record_valid() -> None:
    future = datetime.now(timezone.utc) + timedelta(days=30)
    record = RefreshTokenRecord(
        family_id="fam-001",
        token_hash="abc123",
        user_id="uid-test",
        tenant_id="tenant-abc",
        is_revoked=False,
        expires_at=future,
        revoked_at=None,
    )
    assert record.is_valid()
    assert record.matches("abc123")
    assert not record.matches("wrong-hash")


def test_refresh_token_record_revoked() -> None:
    future = datetime.now(timezone.utc) + timedelta(days=30)
    record = RefreshTokenRecord(
        family_id="fam-001",
        token_hash="abc123",
        user_id="uid-test",
        tenant_id=None,
        is_revoked=True,
        expires_at=future,
        revoked_at=datetime.now(timezone.utc),
    )
    assert not record.is_valid()


def test_refresh_token_record_expired() -> None:
    past = datetime.now(timezone.utc) - timedelta(days=1)
    record = RefreshTokenRecord(
        family_id="fam-001",
        token_hash="abc123",
        user_id="uid-test",
        tenant_id=None,
        is_revoked=False,
        expires_at=past,
        revoked_at=None,
    )
    assert not record.is_valid()


# ---------------------------------------------------------------------------
# hash_token
# ---------------------------------------------------------------------------


def test_hash_token_is_deterministic() -> None:
    from app.core.utils import hash_token

    assert hash_token("same-token") == hash_token("same-token")
    assert hash_token("token-a") != hash_token("token-b")
    assert len(hash_token("x")) == 64  # SHA-256 hex = 64 chars
