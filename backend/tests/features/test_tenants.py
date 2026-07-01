"""
Tests del feature de tenants.

Cubre endpoints REST y casos de uso mediante dependency overrides.
No toca Firebase ni Firestore directamente.
"""

from __future__ import annotations

import time
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient

from app.core.exceptions import ConflictException, NotFoundException
from app.features.tenants.application.use_cases import (
    CreateTenantUseCase,
    GetTenantUseCase,
    ListTenantsUseCase,
    UpdateTenantUseCase,
)
from app.features.tenants.domain.entities import Tenant
from app.features.tenants.presentation.router import (
    _get_create_uc,
    _get_get_uc,
    _get_list_uc,
    _get_update_uc,
)
from app.main import app

_NOW = int(time.time())

_SUPERADMIN_CLAIMS = {
    "sub": "uid-super",
    "tenant_id": None,
    "role": "superadmin",
    "permissions": [],
    "plan": None,
    "type": "access",
    "exp": _NOW + 1800,
    "iat": _NOW,
}

_TENANTADMIN_CLAIMS = {
    "sub": "uid-admin",
    "tenant_id": "tenant-abc",
    "role": "tenantadmin",
    "permissions": ["tenant:read", "tenant:manage"],
    "plan": "professional",
    "type": "access",
    "exp": _NOW + 1800,
    "iat": _NOW,
}

_AUTH_HEADERS = {"Authorization": "Bearer fake-token"}
_DECODE_PATH = "app.dependencies.auth.decode_access_token"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_tenant(
    tenant_id: str = "tenant-abc",
    slug: str = "taller-abc",
    is_active: bool = True,
) -> Tenant:
    now = datetime.now(timezone.utc)
    return Tenant(
        id=tenant_id,
        tenant_id=tenant_id,
        name="Taller ABC",
        slug=slug,
        rut="76.123.456-7",
        plan_id="professional",
        subscription_status="active",
        is_active=is_active,
        is_suspended=False,
        storage_used_bytes=0,
        inspection_count_this_month=0,
        active_user_count=3,
        created_at=now,
        updated_at=now,
        created_by="uid-super",
        updated_by="uid-super",
    )


@pytest.fixture(autouse=True)
def clear_overrides():
    yield
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# POST /tenants
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_tenant_success(client: AsyncClient) -> None:
    mock_uc = AsyncMock(spec=CreateTenantUseCase)
    mock_uc.execute.return_value = _make_tenant()
    app.dependency_overrides[_get_create_uc] = lambda: mock_uc

    with patch(_DECODE_PATH, return_value=_SUPERADMIN_CLAIMS):
        async with client as c:
            response = await c.post(
                "/api/v1/tenants/",
                json={"name": "Taller ABC", "slug": "taller-abc", "rut": "76.123.456-7"},
                headers=_AUTH_HEADERS,
            )

    assert response.status_code == 201
    data = response.json()
    assert data["slug"] == "taller-abc"
    assert data["plan_id"] == "professional"
    mock_uc.execute.assert_called_once()


@pytest.mark.asyncio
async def test_create_tenant_slug_conflict(client: AsyncClient) -> None:
    mock_uc = AsyncMock(spec=CreateTenantUseCase)
    mock_uc.execute.side_effect = ConflictException("El slug 'taller-abc' ya está en uso")
    app.dependency_overrides[_get_create_uc] = lambda: mock_uc

    with patch(_DECODE_PATH, return_value=_SUPERADMIN_CLAIMS):
        async with client as c:
            response = await c.post(
                "/api/v1/tenants/",
                json={"name": "Taller ABC", "slug": "taller-abc", "rut": "76.123.456-7"},
                headers=_AUTH_HEADERS,
            )

    assert response.status_code == 409
    assert response.json()["error_code"] == "CONFLICT"


@pytest.mark.asyncio
async def test_create_tenant_forbidden_for_non_superadmin(client: AsyncClient) -> None:
    with patch(_DECODE_PATH, return_value=_TENANTADMIN_CLAIMS):
        async with client as c:
            response = await c.post(
                "/api/v1/tenants/",
                json={"name": "Nuevo", "slug": "nuevo", "rut": "76.000.001-2"},
                headers=_AUTH_HEADERS,
            )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_create_tenant_missing_required_fields(client: AsyncClient) -> None:
    with patch(_DECODE_PATH, return_value=_SUPERADMIN_CLAIMS):
        async with client as c:
            response = await c.post(
                "/api/v1/tenants/",
                json={"name": "Solo nombre"},
                headers=_AUTH_HEADERS,
            )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_tenant_invalid_slug_format(client: AsyncClient) -> None:
    with patch(_DECODE_PATH, return_value=_SUPERADMIN_CLAIMS):
        async with client as c:
            response = await c.post(
                "/api/v1/tenants/",
                json={"name": "ABC", "slug": "SLUG CON ESPACIOS", "rut": "76.123.456-7"},
                headers=_AUTH_HEADERS,
            )

    assert response.status_code == 422


# ---------------------------------------------------------------------------
# GET /tenants
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_tenants_superadmin(client: AsyncClient) -> None:
    mock_uc = AsyncMock(spec=ListTenantsUseCase)
    mock_uc.execute.return_value = [_make_tenant("t1", "slug-1"), _make_tenant("t2", "slug-2")]
    app.dependency_overrides[_get_list_uc] = lambda: mock_uc

    with patch(_DECODE_PATH, return_value=_SUPERADMIN_CLAIMS):
        async with client as c:
            response = await c.get("/api/v1/tenants/", headers=_AUTH_HEADERS)

    assert response.status_code == 200
    assert len(response.json()) == 2


@pytest.mark.asyncio
async def test_list_tenants_forbidden_for_tenantadmin(client: AsyncClient) -> None:
    with patch(_DECODE_PATH, return_value=_TENANTADMIN_CLAIMS):
        async with client as c:
            response = await c.get("/api/v1/tenants/", headers=_AUTH_HEADERS)

    assert response.status_code == 403


# ---------------------------------------------------------------------------
# GET /tenants/{id}
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_tenant_superadmin_any(client: AsyncClient) -> None:
    mock_uc = AsyncMock(spec=GetTenantUseCase)
    mock_uc.execute.return_value = _make_tenant("tenant-xyz")
    app.dependency_overrides[_get_get_uc] = lambda: mock_uc

    with patch(_DECODE_PATH, return_value=_SUPERADMIN_CLAIMS):
        async with client as c:
            response = await c.get("/api/v1/tenants/tenant-xyz", headers=_AUTH_HEADERS)

    assert response.status_code == 200
    assert response.json()["id"] == "tenant-xyz"


@pytest.mark.asyncio
async def test_get_tenant_tenantadmin_own(client: AsyncClient) -> None:
    mock_uc = AsyncMock(spec=GetTenantUseCase)
    mock_uc.execute.return_value = _make_tenant("tenant-abc")
    app.dependency_overrides[_get_get_uc] = lambda: mock_uc

    with patch(_DECODE_PATH, return_value=_TENANTADMIN_CLAIMS):
        async with client as c:
            response = await c.get("/api/v1/tenants/tenant-abc", headers=_AUTH_HEADERS)

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_get_tenant_tenantadmin_cross_tenant_forbidden(client: AsyncClient) -> None:
    with patch(_DECODE_PATH, return_value=_TENANTADMIN_CLAIMS):
        async with client as c:
            response = await c.get("/api/v1/tenants/tenant-XYZ", headers=_AUTH_HEADERS)

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_get_tenant_not_found(client: AsyncClient) -> None:
    mock_uc = AsyncMock(spec=GetTenantUseCase)
    mock_uc.execute.side_effect = NotFoundException("Taller no encontrado")
    app.dependency_overrides[_get_get_uc] = lambda: mock_uc

    with patch(_DECODE_PATH, return_value=_SUPERADMIN_CLAIMS):
        async with client as c:
            response = await c.get("/api/v1/tenants/no-existe", headers=_AUTH_HEADERS)

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_tenant_unauthenticated(client: AsyncClient) -> None:
    async with client as c:
        response = await c.get("/api/v1/tenants/tenant-abc")
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# PATCH /tenants/{id}
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_update_tenant_success(client: AsyncClient) -> None:
    mock_uc = AsyncMock(spec=UpdateTenantUseCase)
    mock_uc.execute.return_value = _make_tenant()
    app.dependency_overrides[_get_update_uc] = lambda: mock_uc

    with patch(_DECODE_PATH, return_value=_SUPERADMIN_CLAIMS):
        async with client as c:
            response = await c.patch(
                "/api/v1/tenants/tenant-abc",
                json={"name": "Taller Actualizado"},
                headers=_AUTH_HEADERS,
            )

    assert response.status_code == 200
    mock_uc.execute.assert_called_once()


@pytest.mark.asyncio
async def test_update_tenant_not_found(client: AsyncClient) -> None:
    mock_uc = AsyncMock(spec=UpdateTenantUseCase)
    mock_uc.execute.side_effect = NotFoundException("Taller no encontrado")
    app.dependency_overrides[_get_update_uc] = lambda: mock_uc

    with patch(_DECODE_PATH, return_value=_SUPERADMIN_CLAIMS):
        async with client as c:
            response = await c.patch(
                "/api/v1/tenants/no-existe",
                json={"name": "Nombre Válido"},
                headers=_AUTH_HEADERS,
            )

    assert response.status_code == 404


# ---------------------------------------------------------------------------
# GET /tenants/{id}/subscription
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_subscription_success(client: AsyncClient) -> None:
    mock_uc = AsyncMock(spec=GetTenantUseCase)
    mock_uc.execute.return_value = _make_tenant()
    app.dependency_overrides[_get_get_uc] = lambda: mock_uc

    with patch(_DECODE_PATH, return_value=_TENANTADMIN_CLAIMS):
        async with client as c:
            response = await c.get(
                "/api/v1/tenants/tenant-abc/subscription",
                headers=_AUTH_HEADERS,
            )

    assert response.status_code == 200
    data = response.json()
    assert data["plan_id"] == "professional"
    assert "storage_used_bytes" in data
    assert "active_user_count" in data


# ---------------------------------------------------------------------------
# Tenant entity — domain tests
# ---------------------------------------------------------------------------


def test_tenant_is_operational() -> None:
    tenant = _make_tenant()
    assert tenant.is_operational
    assert not tenant.is_deleted


def test_tenant_suspended_not_operational() -> None:
    now = datetime.now(timezone.utc)
    tenant = Tenant(
        id="t", tenant_id="t", name="X", slug="x", rut="1",
        plan_id="basic", subscription_status="active",
        is_active=True, is_suspended=True,
        storage_used_bytes=0, inspection_count_this_month=0, active_user_count=0,
        created_at=now, updated_at=now, created_by="u", updated_by="u",
    )
    assert not tenant.is_operational


def test_tenant_deleted_not_operational() -> None:
    now = datetime.now(timezone.utc)
    tenant = Tenant(
        id="t", tenant_id="t", name="X", slug="x", rut="1",
        plan_id="basic", subscription_status="cancelled",
        is_active=False, is_suspended=False,
        storage_used_bytes=0, inspection_count_this_month=0, active_user_count=0,
        created_at=now, updated_at=now, created_by="u", updated_by="u",
        deleted_at=now,
    )
    assert tenant.is_deleted
    assert not tenant.is_operational
