"""
Tests del feature de clientes.
"""

from __future__ import annotations

import time
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient

from app.core.exceptions import NotFoundException
from app.features.clients.application.use_cases import (
    CreateClientUseCase,
    DeleteClientUseCase,
    GetClientUseCase,
    ListClientsUseCase,
    UpdateClientUseCase,
)
from app.features.clients.domain.entities import Client
from app.features.clients.presentation.router import (
    _get_create_uc,
    _get_delete_uc,
    _get_get_uc,
    _get_list_uc,
    _get_update_uc,
)
from app.main import app

_NOW = int(time.time())
_AUTH_HEADERS = {"Authorization": "Bearer fake-token"}
_DECODE_PATH = "app.dependencies.auth.decode_access_token"

_INSPECTOR_CLAIMS = {
    "sub": "uid-inspector",
    "tenant_id": "tenant-abc",
    "role": "inspector",
    "permissions": ["clients:read", "clients:create", "clients:update", "clients:delete"],
    "plan": "professional",
    "type": "access",
    "exp": _NOW + 1800,
    "iat": _NOW,
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_client(client_id: str = "client-001") -> Client:
    now = datetime.now(timezone.utc)
    return Client(
        id=client_id,
        tenant_id="tenant-abc",
        first_name="María",
        last_name="González",
        full_name="María González",
        email="maria@example.com",
        phone="+56912345678",
        whatsapp="+56912345678",
        rut="12.345.678-9",
        vehicle_count=0,
        inspection_count=0,
        total_spent=0.0,
        last_interaction_at=None,
        created_at=now,
        updated_at=now,
        created_by="uid-inspector",
        updated_by="uid-inspector",
    )


@pytest.fixture(autouse=True)
def clear_overrides():
    yield
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# POST /clients
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_client_success(client: AsyncClient) -> None:
    mock_uc = AsyncMock(spec=CreateClientUseCase)
    mock_uc.execute.return_value = _make_client()
    app.dependency_overrides[_get_create_uc] = lambda: mock_uc

    with patch(_DECODE_PATH, return_value=_INSPECTOR_CLAIMS):
        async with client as c:
            response = await c.post(
                "/api/v1/clients/",
                json={"first_name": "María", "last_name": "González"},
                headers=_AUTH_HEADERS,
            )

    assert response.status_code == 201
    data = response.json()
    assert data["full_name"] == "María González"
    assert data["tenant_id"] == "tenant-abc"
    mock_uc.execute.assert_called_once()


@pytest.mark.asyncio
async def test_create_client_with_all_fields(client: AsyncClient) -> None:
    mock_uc = AsyncMock(spec=CreateClientUseCase)
    mock_uc.execute.return_value = _make_client()
    app.dependency_overrides[_get_create_uc] = lambda: mock_uc

    with patch(_DECODE_PATH, return_value=_INSPECTOR_CLAIMS):
        async with client as c:
            response = await c.post(
                "/api/v1/clients/",
                json={
                    "first_name": "María",
                    "last_name": "González",
                    "email": "maria@example.com",
                    "phone": "+56912345678",
                    "rut": "12.345.678-9",
                },
                headers=_AUTH_HEADERS,
            )

    assert response.status_code == 201


@pytest.mark.asyncio
async def test_create_client_missing_required(client: AsyncClient) -> None:
    with patch(_DECODE_PATH, return_value=_INSPECTOR_CLAIMS):
        async with client as c:
            response = await c.post(
                "/api/v1/clients/",
                json={"first_name": "Solo"},
                headers=_AUTH_HEADERS,
            )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_client_no_permission(client: AsyncClient) -> None:
    with patch(
        _DECODE_PATH,
        return_value={**_INSPECTOR_CLAIMS, "permissions": []},
    ):
        async with client as c:
            response = await c.post(
                "/api/v1/clients/",
                json={"first_name": "X", "last_name": "Y"},
                headers=_AUTH_HEADERS,
            )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_create_client_unauthenticated(client: AsyncClient) -> None:
    async with client as c:
        response = await c.post("/api/v1/clients/", json={})
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# GET /clients
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_clients_success(client: AsyncClient) -> None:
    mock_uc = AsyncMock(spec=ListClientsUseCase)
    mock_uc.execute.return_value = [_make_client("c1"), _make_client("c2")]
    app.dependency_overrides[_get_list_uc] = lambda: mock_uc

    with patch(_DECODE_PATH, return_value=_INSPECTOR_CLAIMS):
        async with client as c:
            response = await c.get("/api/v1/clients/", headers=_AUTH_HEADERS)

    assert response.status_code == 200
    assert len(response.json()) == 2
    mock_uc.execute.assert_called_once_with("tenant-abc", search=None)


@pytest.mark.asyncio
async def test_list_clients_with_search(client: AsyncClient) -> None:
    mock_uc = AsyncMock(spec=ListClientsUseCase)
    mock_uc.execute.return_value = [_make_client()]
    app.dependency_overrides[_get_list_uc] = lambda: mock_uc

    with patch(_DECODE_PATH, return_value=_INSPECTOR_CLAIMS):
        async with client as c:
            response = await c.get(
                "/api/v1/clients/?search=María",
                headers=_AUTH_HEADERS,
            )

    assert response.status_code == 200
    mock_uc.execute.assert_called_once_with("tenant-abc", search="María")


@pytest.mark.asyncio
async def test_list_clients_search_too_short(client: AsyncClient) -> None:
    with patch(_DECODE_PATH, return_value=_INSPECTOR_CLAIMS):
        async with client as c:
            response = await c.get("/api/v1/clients/?search=X", headers=_AUTH_HEADERS)

    assert response.status_code == 422


# ---------------------------------------------------------------------------
# GET /clients/{id}
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_client_success(client: AsyncClient) -> None:
    mock_uc = AsyncMock(spec=GetClientUseCase)
    mock_uc.execute.return_value = _make_client()
    app.dependency_overrides[_get_get_uc] = lambda: mock_uc

    with patch(_DECODE_PATH, return_value=_INSPECTOR_CLAIMS):
        async with client as c:
            response = await c.get("/api/v1/clients/client-001", headers=_AUTH_HEADERS)

    assert response.status_code == 200
    assert response.json()["id"] == "client-001"


@pytest.mark.asyncio
async def test_get_client_not_found(client: AsyncClient) -> None:
    mock_uc = AsyncMock(spec=GetClientUseCase)
    mock_uc.execute.side_effect = NotFoundException("Cliente no encontrado")
    app.dependency_overrides[_get_get_uc] = lambda: mock_uc

    with patch(_DECODE_PATH, return_value=_INSPECTOR_CLAIMS):
        async with client as c:
            response = await c.get("/api/v1/clients/no-existe", headers=_AUTH_HEADERS)

    assert response.status_code == 404


# ---------------------------------------------------------------------------
# PATCH /clients/{id}
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_update_client_success(client: AsyncClient) -> None:
    updated = _make_client()
    mock_uc = AsyncMock(spec=UpdateClientUseCase)
    mock_uc.execute.return_value = updated
    app.dependency_overrides[_get_update_uc] = lambda: mock_uc

    with patch(_DECODE_PATH, return_value=_INSPECTOR_CLAIMS):
        async with client as c:
            response = await c.patch(
                "/api/v1/clients/client-001",
                json={"email": "nuevo@example.com"},
                headers=_AUTH_HEADERS,
            )

    assert response.status_code == 200
    mock_uc.execute.assert_called_once()


@pytest.mark.asyncio
async def test_update_client_not_found(client: AsyncClient) -> None:
    mock_uc = AsyncMock(spec=UpdateClientUseCase)
    mock_uc.execute.side_effect = NotFoundException("Cliente no encontrado")
    app.dependency_overrides[_get_update_uc] = lambda: mock_uc

    with patch(_DECODE_PATH, return_value=_INSPECTOR_CLAIMS):
        async with client as c:
            response = await c.patch(
                "/api/v1/clients/no-existe",
                json={"email": "x@x.com"},
                headers=_AUTH_HEADERS,
            )

    assert response.status_code == 404


# ---------------------------------------------------------------------------
# DELETE /clients/{id}
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_delete_client_success(client: AsyncClient) -> None:
    mock_uc = AsyncMock(spec=DeleteClientUseCase)
    mock_uc.execute.return_value = None
    app.dependency_overrides[_get_delete_uc] = lambda: mock_uc

    with patch(_DECODE_PATH, return_value=_INSPECTOR_CLAIMS):
        async with client as c:
            response = await c.delete("/api/v1/clients/client-001", headers=_AUTH_HEADERS)

    assert response.status_code == 204
    mock_uc.execute.assert_called_once()


@pytest.mark.asyncio
async def test_delete_client_not_found(client: AsyncClient) -> None:
    mock_uc = AsyncMock(spec=DeleteClientUseCase)
    mock_uc.execute.side_effect = NotFoundException("Cliente no encontrado")
    app.dependency_overrides[_get_delete_uc] = lambda: mock_uc

    with patch(_DECODE_PATH, return_value=_INSPECTOR_CLAIMS):
        async with client as c:
            response = await c.delete("/api/v1/clients/no-existe", headers=_AUTH_HEADERS)

    assert response.status_code == 404


# ---------------------------------------------------------------------------
# Client entity — domain tests
# ---------------------------------------------------------------------------


def test_client_is_deleted_when_deleted_at_set() -> None:
    now = datetime.now(timezone.utc)
    c = Client(
        id="c1", tenant_id="t", first_name="A", last_name="B", full_name="A B",
        email=None, phone=None, whatsapp=None, rut=None,
        vehicle_count=0, inspection_count=0, total_spent=0.0,
        last_interaction_at=None,
        created_at=now, updated_at=now, created_by="u", updated_by="u",
        deleted_at=now,
    )
    assert c.is_deleted


def test_client_active_not_deleted() -> None:
    client = _make_client()
    assert not client.is_deleted
