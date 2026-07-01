"""
Tests del feature de vehículos.
"""

from __future__ import annotations

import time
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient

from app.core.exceptions import ConflictException, NotFoundException
from app.features.vehicles.application.use_cases import (
    CreateVehicleUseCase,
    DeleteVehicleUseCase,
    GetVehicleUseCase,
    ListVehiclesUseCase,
    UpdateVehicleUseCase,
    _normalize_plate,
)
from app.features.vehicles.domain.entities import Vehicle
from app.features.vehicles.presentation.router import (
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
    "permissions": ["vehicles:read", "vehicles:create", "vehicles:update", "vehicles:delete"],
    "plan": "professional",
    "type": "access",
    "exp": _NOW + 1800,
    "iat": _NOW,
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_vehicle(vehicle_id: str = "veh-001", plate: str = "ABCD12") -> Vehicle:
    now = datetime.now(timezone.utc)
    return Vehicle(
        id=vehicle_id,
        tenant_id="tenant-abc",
        plate=plate,
        make="Toyota",
        model="Corolla",
        client_id="client-001",
        year=2020,
        color="Blanco",
        vin=None,
        engine="1.8L",
        mileage=50000,
        fuel_type="gasoline",
        transmission_type="automatic",
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
# POST /vehicles
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_vehicle_success(client: AsyncClient) -> None:
    mock_uc = AsyncMock(spec=CreateVehicleUseCase)
    mock_uc.execute.return_value = _make_vehicle()
    app.dependency_overrides[_get_create_uc] = lambda: mock_uc

    with patch(_DECODE_PATH, return_value=_INSPECTOR_CLAIMS):
        async with client as c:
            response = await c.post(
                "/api/v1/vehicles/",
                json={"plate": "AB-CD-12", "make": "Toyota", "model": "Corolla"},
                headers=_AUTH_HEADERS,
            )

    assert response.status_code == 201
    data = response.json()
    assert data["plate"] == "ABCD12"
    mock_uc.execute.assert_called_once()


@pytest.mark.asyncio
async def test_create_vehicle_plate_conflict(client: AsyncClient) -> None:
    mock_uc = AsyncMock(spec=CreateVehicleUseCase)
    mock_uc.execute.side_effect = ConflictException("Ya existe un vehículo con patente 'ABCD12'")
    app.dependency_overrides[_get_create_uc] = lambda: mock_uc

    with patch(_DECODE_PATH, return_value=_INSPECTOR_CLAIMS):
        async with client as c:
            response = await c.post(
                "/api/v1/vehicles/",
                json={"plate": "AB-CD-12", "make": "Toyota", "model": "Corolla"},
                headers=_AUTH_HEADERS,
            )

    assert response.status_code == 409


@pytest.mark.asyncio
async def test_create_vehicle_missing_required(client: AsyncClient) -> None:
    with patch(_DECODE_PATH, return_value=_INSPECTOR_CLAIMS):
        async with client as c:
            response = await c.post(
                "/api/v1/vehicles/",
                json={"plate": "ABCD12"},
                headers=_AUTH_HEADERS,
            )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_vehicle_no_permission(client: AsyncClient) -> None:
    with patch(
        _DECODE_PATH,
        return_value={**_INSPECTOR_CLAIMS, "permissions": ["vehicles:read"]},
    ):
        async with client as c:
            response = await c.post(
                "/api/v1/vehicles/",
                json={"plate": "ABCD12", "make": "Toyota", "model": "Corolla"},
                headers=_AUTH_HEADERS,
            )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_create_vehicle_with_all_fields(client: AsyncClient) -> None:
    mock_uc = AsyncMock(spec=CreateVehicleUseCase)
    mock_uc.execute.return_value = _make_vehicle()
    app.dependency_overrides[_get_create_uc] = lambda: mock_uc

    with patch(_DECODE_PATH, return_value=_INSPECTOR_CLAIMS):
        async with client as c:
            response = await c.post(
                "/api/v1/vehicles/",
                json={
                    "plate": "ABCD12",
                    "make": "Toyota",
                    "model": "Corolla",
                    "year": 2020,
                    "color": "Blanco",
                    "mileage": 50000,
                    "fuel_type": "gasoline",
                    "transmission_type": "automatic",
                },
                headers=_AUTH_HEADERS,
            )

    assert response.status_code == 201


# ---------------------------------------------------------------------------
# GET /vehicles
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_vehicles_success(client: AsyncClient) -> None:
    mock_uc = AsyncMock(spec=ListVehiclesUseCase)
    mock_uc.execute.return_value = [_make_vehicle("v1"), _make_vehicle("v2", "ZZXX99")]
    app.dependency_overrides[_get_list_uc] = lambda: mock_uc

    with patch(_DECODE_PATH, return_value=_INSPECTOR_CLAIMS):
        async with client as c:
            response = await c.get("/api/v1/vehicles/", headers=_AUTH_HEADERS)

    assert response.status_code == 200
    assert len(response.json()) == 2


@pytest.mark.asyncio
async def test_list_vehicles_filter_by_client(client: AsyncClient) -> None:
    mock_uc = AsyncMock(spec=ListVehiclesUseCase)
    mock_uc.execute.return_value = [_make_vehicle()]
    app.dependency_overrides[_get_list_uc] = lambda: mock_uc

    with patch(_DECODE_PATH, return_value=_INSPECTOR_CLAIMS):
        async with client as c:
            response = await c.get(
                "/api/v1/vehicles/?client_id=client-001",
                headers=_AUTH_HEADERS,
            )

    assert response.status_code == 200
    mock_uc.execute.assert_called_once_with("tenant-abc", client_id="client-001", search=None)


@pytest.mark.asyncio
async def test_list_vehicles_with_search(client: AsyncClient) -> None:
    mock_uc = AsyncMock(spec=ListVehiclesUseCase)
    mock_uc.execute.return_value = [_make_vehicle()]
    app.dependency_overrides[_get_list_uc] = lambda: mock_uc

    with patch(_DECODE_PATH, return_value=_INSPECTOR_CLAIMS):
        async with client as c:
            response = await c.get(
                "/api/v1/vehicles/?search=Toyota",
                headers=_AUTH_HEADERS,
            )

    assert response.status_code == 200
    mock_uc.execute.assert_called_once_with("tenant-abc", client_id=None, search="Toyota")


# ---------------------------------------------------------------------------
# GET /vehicles/{id}
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_vehicle_success(client: AsyncClient) -> None:
    mock_uc = AsyncMock(spec=GetVehicleUseCase)
    mock_uc.execute.return_value = _make_vehicle()
    app.dependency_overrides[_get_get_uc] = lambda: mock_uc

    with patch(_DECODE_PATH, return_value=_INSPECTOR_CLAIMS):
        async with client as c:
            response = await c.get("/api/v1/vehicles/veh-001", headers=_AUTH_HEADERS)

    assert response.status_code == 200
    assert response.json()["plate"] == "ABCD12"


@pytest.mark.asyncio
async def test_get_vehicle_not_found(client: AsyncClient) -> None:
    mock_uc = AsyncMock(spec=GetVehicleUseCase)
    mock_uc.execute.side_effect = NotFoundException("Vehículo no encontrado")
    app.dependency_overrides[_get_get_uc] = lambda: mock_uc

    with patch(_DECODE_PATH, return_value=_INSPECTOR_CLAIMS):
        async with client as c:
            response = await c.get("/api/v1/vehicles/no-existe", headers=_AUTH_HEADERS)

    assert response.status_code == 404


# ---------------------------------------------------------------------------
# PATCH /vehicles/{id}
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_update_vehicle_success(client: AsyncClient) -> None:
    mock_uc = AsyncMock(spec=UpdateVehicleUseCase)
    mock_uc.execute.return_value = _make_vehicle()
    app.dependency_overrides[_get_update_uc] = lambda: mock_uc

    with patch(_DECODE_PATH, return_value=_INSPECTOR_CLAIMS):
        async with client as c:
            response = await c.patch(
                "/api/v1/vehicles/veh-001",
                json={"mileage": 60000},
                headers=_AUTH_HEADERS,
            )

    assert response.status_code == 200
    mock_uc.execute.assert_called_once()


# ---------------------------------------------------------------------------
# DELETE /vehicles/{id}
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_delete_vehicle_success(client: AsyncClient) -> None:
    mock_uc = AsyncMock(spec=DeleteVehicleUseCase)
    mock_uc.execute.return_value = None
    app.dependency_overrides[_get_delete_uc] = lambda: mock_uc

    with patch(_DECODE_PATH, return_value=_INSPECTOR_CLAIMS):
        async with client as c:
            response = await c.delete("/api/v1/vehicles/veh-001", headers=_AUTH_HEADERS)

    assert response.status_code == 204


@pytest.mark.asyncio
async def test_delete_vehicle_not_found(client: AsyncClient) -> None:
    mock_uc = AsyncMock(spec=DeleteVehicleUseCase)
    mock_uc.execute.side_effect = NotFoundException("Vehículo no encontrado")
    app.dependency_overrides[_get_delete_uc] = lambda: mock_uc

    with patch(_DECODE_PATH, return_value=_INSPECTOR_CLAIMS):
        async with client as c:
            response = await c.delete("/api/v1/vehicles/no-existe", headers=_AUTH_HEADERS)

    assert response.status_code == 404


# ---------------------------------------------------------------------------
# Plate normalization — domain logic
# ---------------------------------------------------------------------------


def test_normalize_plate_removes_hyphens() -> None:
    assert _normalize_plate("AB-CD-12") == "ABCD12"


def test_normalize_plate_uppercases() -> None:
    assert _normalize_plate("abcd12") == "ABCD12"


def test_normalize_plate_removes_spaces() -> None:
    assert _normalize_plate("AB CD 12") == "ABCD12"


def test_normalize_plate_new_format() -> None:
    assert _normalize_plate("bbbb-12") == "BBBB12"


def test_normalize_plate_already_normalized() -> None:
    assert _normalize_plate("ABCD12") == "ABCD12"


# ---------------------------------------------------------------------------
# Vehicle entity — domain tests
# ---------------------------------------------------------------------------


def test_vehicle_is_deleted_when_deleted_at_set() -> None:
    now = datetime.now(timezone.utc)
    v = Vehicle(
        id="v1", tenant_id="t", plate="X", make="X", model="X",
        client_id=None, year=None, color=None, vin=None, engine=None,
        mileage=None, fuel_type=None, transmission_type=None,
        created_at=now, updated_at=now, created_by="u", updated_by="u",
        deleted_at=now,
    )
    assert v.is_deleted


def test_vehicle_active_not_deleted() -> None:
    v = _make_vehicle()
    assert not v.is_deleted
