"""
Tests de smoke y middleware para la aplicación FastAPI.

Verifica: health checks, cabeceras de seguridad, rate limiting,
manejo de excepciones y estructura de respuestas.
"""

from __future__ import annotations

import time
from datetime import timedelta
from unittest.mock import patch

import pytest
from httpx import ASGITransport, AsyncClient

from tests.conftest import JWT_TEST_SECRET


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_jwt_settings():
    """Parche de settings de JWT para tests unitarios de security.py."""
    with patch("app.core.security.settings") as mock:
        mock.JWT_SECRET_KEY = JWT_TEST_SECRET
        mock.JWT_ALGORITHM = "HS256"
        mock.ACCESS_TOKEN_EXPIRE_MINUTES = 30
        mock.REFRESH_TOKEN_EXPIRE_DAYS = 30
        yield mock


# ---------------------------------------------------------------------------
# Health checks
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_health_v1(client: AsyncClient) -> None:
    async with client as c:
        response = await c.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["api"] == "v1"


@pytest.mark.asyncio
async def test_health_v2(client: AsyncClient) -> None:
    async with client as c:
        response = await c.get("/api/v2/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["api"] == "v2"


@pytest.mark.asyncio
async def test_openapi_accessible(client: AsyncClient) -> None:
    async with client as c:
        response = await c.get("/api/v1/openapi.json")
    assert response.status_code == 200


# ---------------------------------------------------------------------------
# Cabeceras de seguridad
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_security_headers_present(client: AsyncClient) -> None:
    async with client as c:
        response = await c.get("/api/v1/health")
    assert response.headers.get("x-frame-options") == "DENY"
    assert response.headers.get("x-content-type-options") == "nosniff"
    assert response.headers.get("x-xss-protection") == "1; mode=block"
    assert "strict-transport-security" in response.headers
    assert "content-security-policy" in response.headers
    assert "referrer-policy" in response.headers


# ---------------------------------------------------------------------------
# Manejo de excepciones
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_404_not_found(client: AsyncClient) -> None:
    async with client as c:
        response = await c.get("/api/v1/ruta-que-no-existe")
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# Rate limiting
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_rate_limit_returns_429_after_limit() -> None:
    """Verifica que el rate limiter retorna 429 al superar el límite configurado."""
    from fastapi import FastAPI

    from app.middleware.rate_limit import RateLimitMiddleware

    test_app = FastAPI()
    test_app.add_middleware(RateLimitMiddleware)

    @test_app.get("/ping")
    async def ping() -> dict:
        return {"pong": True}

    with patch("app.middleware.rate_limit.settings") as mock_settings:
        mock_settings.RATE_LIMIT_CALLS = 2
        mock_settings.RATE_LIMIT_AUTH_CALLS = 2
        mock_settings.RATE_LIMIT_PERIOD_SECONDS = 60

        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as c:
            r1 = await c.get("/ping")
            r2 = await c.get("/ping")
            r3 = await c.get("/ping")

    assert r1.status_code == 200
    assert r2.status_code == 200
    assert r3.status_code == 429
    assert r3.json()["error_code"] == "RATE_LIMIT_EXCEEDED"
    assert "Retry-After" in r3.headers


# ---------------------------------------------------------------------------
# Módulo de seguridad (JWT)
# ---------------------------------------------------------------------------


def test_create_and_decode_access_token(mock_jwt_settings) -> None:
    from app.core.security import create_access_token, decode_access_token

    token = create_access_token(
        subject="uid-test-123",
        tenant_id="tenant-abc",
        role="inspector",
        permissions=["inspections:read", "inspections:create"],
        plan="professional",
    )
    payload = decode_access_token(token)

    assert payload["sub"] == "uid-test-123"
    assert payload["tenant_id"] == "tenant-abc"
    assert payload["role"] == "inspector"
    assert "inspections:read" in payload["permissions"]
    assert payload["type"] == "access"


def test_decode_refresh_token_rejected_as_access(mock_jwt_settings) -> None:
    from app.core.exceptions import UnauthorizedException
    from app.core.security import create_refresh_token, decode_access_token

    refresh = create_refresh_token(
        subject="uid-test-123",
        tenant_id="tenant-abc",
        token_family="family-001",
    )
    with pytest.raises(UnauthorizedException, match="Tipo de token incorrecto"):
        decode_access_token(refresh)


def test_invalid_token_raises_unauthorized(mock_jwt_settings) -> None:
    from app.core.exceptions import UnauthorizedException
    from app.core.security import decode_token

    with pytest.raises(UnauthorizedException, match="Token inválido"):
        decode_token("not.a.valid.jwt")


def test_expired_token_raises_unauthorized() -> None:
    from app.core.exceptions import UnauthorizedException
    from app.core.security import create_access_token, decode_access_token

    with patch("app.core.security.settings") as mock:
        mock.JWT_SECRET_KEY = JWT_TEST_SECRET
        mock.JWT_ALGORITHM = "HS256"
        mock.ACCESS_TOKEN_EXPIRE_MINUTES = 30

        token = create_access_token(
            subject="uid-expired",
            tenant_id=None,
            role="superadmin",
            permissions=[],
            expires_delta=timedelta(seconds=-1),
        )

        with pytest.raises(UnauthorizedException, match="Token expirado"):
            decode_access_token(token)


# ---------------------------------------------------------------------------
# Schemas — TokenPayload
# ---------------------------------------------------------------------------


def test_token_payload_superadmin_has_all_permissions() -> None:
    from app.schemas.auth import TokenPayload

    now = int(time.time())
    user = TokenPayload(
        sub="uid-super",
        role="superadmin",
        permissions=[],
        exp=now + 1800,
        iat=now,
    )
    assert user.is_superadmin
    assert user.has_permission("any:permission:at:all")


def test_token_payload_inspector_limited_permissions() -> None:
    from app.schemas.auth import TokenPayload

    now = int(time.time())
    user = TokenPayload(
        sub="uid-insp",
        tenant_id="tenant-abc",
        role="inspector",
        permissions=["inspections:read"],
        exp=now + 1800,
        iat=now,
    )
    assert not user.is_superadmin
    assert user.has_permission("inspections:read")
    assert not user.has_permission("inspections:delete")
    assert user.has_tenant
