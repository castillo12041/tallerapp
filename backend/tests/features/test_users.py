"""
Tests del feature de usuarios.

Cubre endpoints REST, casos de uso y entidades de dominio
mediante dependency overrides. Sin acceso real a Firebase o Firestore.
"""

from __future__ import annotations

import time
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient

from app.core.exceptions import ConflictException, ForbiddenException, NotFoundException
from app.features.users.application.use_cases import (
    CreateUserUseCase,
    DeactivateUserUseCase,
    GetUserUseCase,
    ListUsersUseCase,
    UpdateUserUseCase,
)
from app.features.users.domain.entities import User
from app.features.users.presentation.router import (
    _get_create_uc,
    _get_deactivate_uc,
    _get_get_uc,
    _get_list_uc,
    _get_update_uc,
)
from app.main import app

_NOW = int(time.time())
_AUTH_HEADERS = {"Authorization": "Bearer fake-token"}
_DECODE_PATH = "app.dependencies.auth.decode_access_token"

_TENANTADMIN_CLAIMS = {
    "sub": "uid-admin",
    "tenant_id": "tenant-abc",
    "role": "tenantadmin",
    "permissions": ["users:read", "users:create", "users:update", "users:delete"],
    "plan": "professional",
    "type": "access",
    "exp": _NOW + 1800,
    "iat": _NOW,
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_user(uid: str = "uid-inspector", role: str = "inspector") -> User:
    now = datetime.now(timezone.utc)
    return User(
        uid=uid,
        email=f"{uid}@example.com",
        display_name="Juan Inspector",
        first_name="Juan",
        last_name="Inspector",
        role=role,
        permissions=["inspections:read"],
        tenant_id="tenant-abc",
        plan="professional",
        is_active=True,
        phone="+56912345678",
        created_at=now,
        updated_at=now,
        created_by="uid-admin",
        updated_by="uid-admin",
    )


@pytest.fixture(autouse=True)
def clear_overrides():
    yield
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# POST /users
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_user_success(client: AsyncClient) -> None:
    mock_uc = AsyncMock(spec=CreateUserUseCase)
    mock_uc.execute.return_value = _make_user()
    app.dependency_overrides[_get_create_uc] = lambda: mock_uc

    with patch(_DECODE_PATH, return_value=_TENANTADMIN_CLAIMS):
        async with client as c:
            response = await c.post(
                "/api/v1/users/",
                json={
                    "email": "juan@example.com",
                    "display_name": "Juan Inspector",
                    "first_name": "Juan",
                    "last_name": "Inspector",
                    "password": "Segura123!",
                    "role": "inspector",
                },
                headers=_AUTH_HEADERS,
            )

    assert response.status_code == 201
    data = response.json()
    assert data["role"] == "inspector"
    assert data["tenant_id"] == "tenant-abc"
    assert "password" not in data
    mock_uc.execute.assert_called_once()


@pytest.mark.asyncio
async def test_create_user_email_conflict(client: AsyncClient) -> None:
    mock_uc = AsyncMock(spec=CreateUserUseCase)
    mock_uc.execute.side_effect = ConflictException("El email 'x@x.com' ya está registrado")
    app.dependency_overrides[_get_create_uc] = lambda: mock_uc

    with patch(_DECODE_PATH, return_value=_TENANTADMIN_CLAIMS):
        async with client as c:
            response = await c.post(
                "/api/v1/users/",
                json={
                    "email": "duplicado@example.com",
                    "display_name": "Usuario Duplicado",
                    "first_name": "Usuario",
                    "last_name": "Duplicado",
                    "password": "Segura123!",
                    "role": "inspector",
                },
                headers=_AUTH_HEADERS,
            )

    assert response.status_code == 409
    assert response.json()["error_code"] == "CONFLICT"


@pytest.mark.asyncio
async def test_create_user_missing_required(client: AsyncClient) -> None:
    with patch(_DECODE_PATH, return_value=_TENANTADMIN_CLAIMS):
        async with client as c:
            response = await c.post(
                "/api/v1/users/",
                json={"email": "x@x.com"},
                headers=_AUTH_HEADERS,
            )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_user_no_permission(client: AsyncClient) -> None:
    with patch(
        _DECODE_PATH,
        return_value={
            **_TENANTADMIN_CLAIMS,
            "role": "inspector",
            "permissions": ["inspections:read"],
        },
    ):
        async with client as c:
            response = await c.post(
                "/api/v1/users/",
                json={
                    "email": "x@x.com",
                    "display_name": "X",
                    "first_name": "X",
                    "last_name": "X",
                    "password": "Segura123!",
                    "role": "inspector",
                },
                headers=_AUTH_HEADERS,
            )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_create_user_unauthenticated(client: AsyncClient) -> None:
    async with client as c:
        response = await c.post("/api/v1/users/", json={})
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# GET /users
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_users_success(client: AsyncClient) -> None:
    mock_uc = AsyncMock(spec=ListUsersUseCase)
    mock_uc.execute.return_value = [_make_user("u1"), _make_user("u2")]
    app.dependency_overrides[_get_list_uc] = lambda: mock_uc

    with patch(_DECODE_PATH, return_value=_TENANTADMIN_CLAIMS):
        async with client as c:
            response = await c.get("/api/v1/users/", headers=_AUTH_HEADERS)

    assert response.status_code == 200
    assert len(response.json()) == 2
    mock_uc.execute.assert_called_once_with("tenant-abc")


# ---------------------------------------------------------------------------
# GET /users/{uid}
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_user_success(client: AsyncClient) -> None:
    mock_uc = AsyncMock(spec=GetUserUseCase)
    mock_uc.execute.return_value = _make_user("uid-inspector")
    app.dependency_overrides[_get_get_uc] = lambda: mock_uc

    with patch(_DECODE_PATH, return_value=_TENANTADMIN_CLAIMS):
        async with client as c:
            response = await c.get("/api/v1/users/uid-inspector", headers=_AUTH_HEADERS)

    assert response.status_code == 200
    assert response.json()["uid"] == "uid-inspector"


@pytest.mark.asyncio
async def test_get_user_not_found(client: AsyncClient) -> None:
    mock_uc = AsyncMock(spec=GetUserUseCase)
    mock_uc.execute.side_effect = NotFoundException("Usuario no encontrado")
    app.dependency_overrides[_get_get_uc] = lambda: mock_uc

    with patch(_DECODE_PATH, return_value=_TENANTADMIN_CLAIMS):
        async with client as c:
            response = await c.get("/api/v1/users/no-existe", headers=_AUTH_HEADERS)

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_own_user_without_permission(client: AsyncClient) -> None:
    mock_uc = AsyncMock(spec=GetUserUseCase)
    mock_uc.execute.return_value = _make_user("uid-self")
    app.dependency_overrides[_get_get_uc] = lambda: mock_uc

    with patch(
        _DECODE_PATH,
        return_value={
            **_TENANTADMIN_CLAIMS,
            "sub": "uid-self",
            "role": "inspector",
            "permissions": [],
        },
    ):
        async with client as c:
            response = await c.get("/api/v1/users/uid-self", headers=_AUTH_HEADERS)

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_get_other_user_without_permission_forbidden(client: AsyncClient) -> None:
    with patch(
        _DECODE_PATH,
        return_value={
            **_TENANTADMIN_CLAIMS,
            "sub": "uid-self",
            "role": "inspector",
            "permissions": [],
        },
    ):
        async with client as c:
            response = await c.get("/api/v1/users/uid-other", headers=_AUTH_HEADERS)

    assert response.status_code == 403


# ---------------------------------------------------------------------------
# PATCH /users/{uid}
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_update_user_success(client: AsyncClient) -> None:
    mock_uc = AsyncMock(spec=UpdateUserUseCase)
    mock_uc.execute.return_value = _make_user()
    app.dependency_overrides[_get_update_uc] = lambda: mock_uc

    with patch(_DECODE_PATH, return_value=_TENANTADMIN_CLAIMS):
        async with client as c:
            response = await c.patch(
                "/api/v1/users/uid-inspector",
                json={"display_name": "Juan Actualizado"},
                headers=_AUTH_HEADERS,
            )

    assert response.status_code == 200
    mock_uc.execute.assert_called_once()


@pytest.mark.asyncio
async def test_update_user_role_change(client: AsyncClient) -> None:
    mock_uc = AsyncMock(spec=UpdateUserUseCase)
    mock_uc.execute.return_value = _make_user(role="mechanic")
    app.dependency_overrides[_get_update_uc] = lambda: mock_uc

    with patch(_DECODE_PATH, return_value=_TENANTADMIN_CLAIMS):
        async with client as c:
            response = await c.patch(
                "/api/v1/users/uid-inspector",
                json={"role": "mechanic"},
                headers=_AUTH_HEADERS,
            )

    assert response.status_code == 200


# ---------------------------------------------------------------------------
# DELETE /users/{uid}
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_deactivate_user_success(client: AsyncClient) -> None:
    mock_uc = AsyncMock(spec=DeactivateUserUseCase)
    mock_uc.execute.return_value = None
    app.dependency_overrides[_get_deactivate_uc] = lambda: mock_uc

    with patch(_DECODE_PATH, return_value=_TENANTADMIN_CLAIMS):
        async with client as c:
            response = await c.delete(
                "/api/v1/users/uid-inspector",
                headers=_AUTH_HEADERS,
            )

    assert response.status_code == 204
    mock_uc.execute.assert_called_once()


@pytest.mark.asyncio
async def test_deactivate_user_not_found(client: AsyncClient) -> None:
    mock_uc = AsyncMock(spec=DeactivateUserUseCase)
    mock_uc.execute.side_effect = NotFoundException("Usuario no encontrado")
    app.dependency_overrides[_get_deactivate_uc] = lambda: mock_uc

    with patch(_DECODE_PATH, return_value=_TENANTADMIN_CLAIMS):
        async with client as c:
            response = await c.delete(
                "/api/v1/users/no-existe",
                headers=_AUTH_HEADERS,
            )

    assert response.status_code == 404


# ---------------------------------------------------------------------------
# GET /roles y GET /permissions
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_roles_authenticated(client: AsyncClient) -> None:
    with patch(_DECODE_PATH, return_value=_TENANTADMIN_CLAIMS):
        async with client as c:
            response = await c.get("/api/v1/roles", headers=_AUTH_HEADERS)

    assert response.status_code == 200
    codes = [r["code"] for r in response.json()]
    assert "superadmin" in codes
    assert "inspector" in codes
    assert "customer" in codes
    assert len(codes) == 7


@pytest.mark.asyncio
async def test_list_permissions_authenticated(client: AsyncClient) -> None:
    with patch(_DECODE_PATH, return_value=_TENANTADMIN_CLAIMS):
        async with client as c:
            response = await c.get("/api/v1/permissions", headers=_AUTH_HEADERS)

    assert response.status_code == 200
    ids = [p["id"] for p in response.json()]
    assert "inspections:create" in ids
    assert "users:delete" in ids
    assert "pdf:generate" in ids
    assert len(ids) == 44


@pytest.mark.asyncio
async def test_list_roles_requires_auth(client: AsyncClient) -> None:
    async with client as c:
        response = await c.get("/api/v1/roles")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_list_permissions_requires_auth(client: AsyncClient) -> None:
    async with client as c:
        response = await c.get("/api/v1/permissions")
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# User entity — domain tests
# ---------------------------------------------------------------------------


def test_user_is_deleted_when_deleted_at_set() -> None:
    now = datetime.now(timezone.utc)
    user = User(
        uid="u1", email="u@u.com", display_name="U",
        first_name="U", last_name="U", role="inspector",
        permissions=[], tenant_id="t", plan=None,
        is_active=False, phone=None,
        created_at=now, updated_at=now,
        created_by="admin", updated_by="admin",
        deleted_at=now,
    )
    assert user.is_deleted


def test_user_active_not_deleted() -> None:
    user = _make_user()
    assert not user.is_deleted
    assert user.is_active
