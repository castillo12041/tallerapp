"""
Tests del feature de agenda/citas (Fase 14).

Repositorios y use cases se mockean completamente.
Se testea: CRUD, workflow, conflictos de horario, filtros, disponibilidad.
"""

from __future__ import annotations

import time
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient

from app.core.exceptions import ConflictException, NotFoundException
from app.features.appointments.application.use_cases import (
    CreateAppointmentUseCase,
    DeleteAppointmentUseCase,
    GetAppointmentUseCase,
    GetAvailabilityUseCase,
    ListAppointmentsUseCase,
    UpdateAppointmentUseCase,
)
from app.features.appointments.application.workflow_use_cases import (
    CancelAppointmentUseCase,
    ConfirmAppointmentUseCase,
)
from app.features.appointments.domain.entities import Appointment
from app.features.appointments.domain.workflow import (
    STATUS_CANCELLED,
    STATUS_CONFIRMED,
    STATUS_SCHEDULED,
    validate_transition,
)
from app.features.appointments.infrastructure.appointment_repository import (
    AppointmentRepository,
)
from app.features.appointments.presentation.router import (
    _get_availability_uc,
    _get_cancel_uc,
    _get_confirm_uc,
    _get_create_uc,
    _get_delete_uc,
    _get_get_uc,
    _get_list_uc,
    _get_update_uc,
)
from app.main import app

_NOW = int(time.time())
_AUTH = {"Authorization": "Bearer fake-token"}
_DECODE_PATH = "app.dependencies.auth.decode_access_token"

_USER_CLAIMS = {
    "sub": "uid-manager",
    "tenant_id": "tenant-abc",
    "role": "workshopmanager",
    "permissions": [
        "calendar:read",
        "calendar:create",
        "calendar:update",
        "calendar:delete",
    ],
    "plan": "professional",
    "type": "access",
    "exp": _NOW + 1800,
    "iat": _NOW,
}

_START = datetime(2026, 7, 10, 9, 0, tzinfo=timezone.utc)
_END = datetime(2026, 7, 10, 10, 0, tzinfo=timezone.utc)
_CREATED = datetime(2026, 7, 1, 8, 0, tzinfo=timezone.utc)


def _make_appt(**overrides) -> Appointment:
    defaults = dict(
        id="appt-1",
        tenant_id="tenant-abc",
        type="appointment",
        status=STATUS_SCHEDULED,
        title="Revisión preventiva",
        start_at=_START,
        end_at=_END,
        all_day=False,
        client_id="client-1",
        vehicle_id="vehicle-1",
        mechanic_id="mech-1",
        mechanic_name="Juan Pérez",
        inspection_id=None,
        work_order_id=None,
        notes="Traer ficha anterior",
        reminder_minutes=30,
        cancel_reason=None,
        cancelled_at=None,
        deleted_at=None,
        created_at=_CREATED,
        updated_at=_CREATED,
        created_by="uid-manager",
        updated_by="uid-manager",
    )
    defaults.update(overrides)
    return Appointment(**defaults)


# ---------------------------------------------------------------------------
# Domain — workflow
# ---------------------------------------------------------------------------


def test_valid_transitions():
    validate_transition(STATUS_SCHEDULED, STATUS_CONFIRMED)
    validate_transition(STATUS_SCHEDULED, STATUS_CANCELLED)
    validate_transition(STATUS_CONFIRMED, STATUS_CANCELLED)


def test_invalid_transition_raises():
    with pytest.raises(ConflictException):
        validate_transition(STATUS_CANCELLED, STATUS_CONFIRMED)


def test_invalid_transition_completed_to_any():
    with pytest.raises(ConflictException):
        validate_transition("completed", STATUS_SCHEDULED)


# ---------------------------------------------------------------------------
# Domain — entity properties
# ---------------------------------------------------------------------------


def test_is_terminal_for_cancelled():
    appt = _make_appt(status=STATUS_CANCELLED)
    assert appt.is_terminal is True


def test_is_terminal_for_scheduled():
    appt = _make_appt(status=STATUS_SCHEDULED)
    assert appt.is_terminal is False


def test_duration_minutes():
    appt = _make_appt()
    assert appt.duration_minutes == 60


def test_is_deleted_false_when_no_deleted_at():
    appt = _make_appt()
    assert appt.is_deleted is False


# ---------------------------------------------------------------------------
# POST /appointments
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_create_appointment_success(client: AsyncClient):
    appt = _make_appt()
    mock_uc = AsyncMock(spec=CreateAppointmentUseCase)
    mock_uc.execute.return_value = appt

    with patch(_DECODE_PATH, return_value=_USER_CLAIMS):
        app.dependency_overrides[_get_create_uc] = lambda: mock_uc
        resp = await client.post(
            "/api/v1/appointments",
            headers=_AUTH,
            json={
                "type": "appointment",
                "title": "Revisión preventiva",
                "start_at": _START.isoformat(),
                "end_at": _END.isoformat(),
                "mechanic_id": "mech-1",
                "mechanic_name": "Juan Pérez",
            },
        )
    app.dependency_overrides.pop(_get_create_uc, None)
    assert resp.status_code == 201
    assert resp.json()["id"] == "appt-1"
    assert resp.json()["status"] == STATUS_SCHEDULED


@pytest.mark.anyio
async def test_create_appointment_end_before_start_fails(client: AsyncClient):
    with patch(_DECODE_PATH, return_value=_USER_CLAIMS):
        resp = await client.post(
            "/api/v1/appointments",
            headers=_AUTH,
            json={
                "type": "appointment",
                "title": "Test",
                "start_at": _END.isoformat(),
                "end_at": _START.isoformat(),
            },
        )
    assert resp.status_code == 422


@pytest.mark.anyio
async def test_create_appointment_conflict_raises_409(client: AsyncClient):
    mock_uc = AsyncMock(spec=CreateAppointmentUseCase)
    mock_uc.execute.side_effect = ConflictException("El mecánico tiene citas superpuestas")

    with patch(_DECODE_PATH, return_value=_USER_CLAIMS):
        app.dependency_overrides[_get_create_uc] = lambda: mock_uc
        resp = await client.post(
            "/api/v1/appointments",
            headers=_AUTH,
            json={
                "type": "appointment",
                "title": "Test conflicto",
                "start_at": _START.isoformat(),
                "end_at": _END.isoformat(),
                "mechanic_id": "mech-1",
            },
        )
    app.dependency_overrides.pop(_get_create_uc, None)
    assert resp.status_code == 409


# ---------------------------------------------------------------------------
# GET /appointments
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_list_appointments(client: AsyncClient):
    mock_uc = AsyncMock(spec=ListAppointmentsUseCase)
    mock_uc.execute.return_value = [_make_appt(), _make_appt(id="appt-2", title="OT")]

    with patch(_DECODE_PATH, return_value=_USER_CLAIMS):
        app.dependency_overrides[_get_list_uc] = lambda: mock_uc
        resp = await client.get("/api/v1/appointments", headers=_AUTH)
    app.dependency_overrides.pop(_get_list_uc, None)

    assert resp.status_code == 200
    assert resp.json()["total"] == 2


@pytest.mark.anyio
async def test_list_appointments_filtered_by_date(client: AsyncClient):
    mock_uc = AsyncMock(spec=ListAppointmentsUseCase)
    mock_uc.execute.return_value = [_make_appt()]

    with patch(_DECODE_PATH, return_value=_USER_CLAIMS):
        app.dependency_overrides[_get_list_uc] = lambda: mock_uc
        resp = await client.get(
            "/api/v1/appointments?date=2026-07-10&mechanic_id=mech-1",
            headers=_AUTH,
        )
    app.dependency_overrides.pop(_get_list_uc, None)

    assert resp.status_code == 200
    mock_uc.execute.assert_awaited_once()
    kwargs = mock_uc.execute.call_args.kwargs
    assert kwargs["mechanic_id"] == "mech-1"


# ---------------------------------------------------------------------------
# GET /appointments/{id}
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_get_appointment_not_found(client: AsyncClient):
    mock_uc = AsyncMock(spec=GetAppointmentUseCase)
    mock_uc.execute.side_effect = NotFoundException("Cita no encontrada")

    with patch(_DECODE_PATH, return_value=_USER_CLAIMS):
        app.dependency_overrides[_get_get_uc] = lambda: mock_uc
        resp = await client.get("/api/v1/appointments/not-exist", headers=_AUTH)
    app.dependency_overrides.pop(_get_get_uc, None)
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# PATCH /appointments/{id}
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_update_appointment_success(client: AsyncClient):
    updated = _make_appt(title="Revisión actualizada")
    mock_uc = AsyncMock(spec=UpdateAppointmentUseCase)
    mock_uc.execute.return_value = updated

    with patch(_DECODE_PATH, return_value=_USER_CLAIMS):
        app.dependency_overrides[_get_update_uc] = lambda: mock_uc
        resp = await client.patch(
            "/api/v1/appointments/appt-1",
            headers=_AUTH,
            json={"title": "Revisión actualizada"},
        )
    app.dependency_overrides.pop(_get_update_uc, None)
    assert resp.status_code == 200
    assert resp.json()["title"] == "Revisión actualizada"


@pytest.mark.anyio
async def test_update_terminal_appointment_raises(client: AsyncClient):
    mock_uc = AsyncMock(spec=UpdateAppointmentUseCase)
    mock_uc.execute.side_effect = ConflictException("No se puede editar una cita cancelada")

    with patch(_DECODE_PATH, return_value=_USER_CLAIMS):
        app.dependency_overrides[_get_update_uc] = lambda: mock_uc
        resp = await client.patch(
            "/api/v1/appointments/appt-1",
            headers=_AUTH,
            json={"title": "Test"},
        )
    app.dependency_overrides.pop(_get_update_uc, None)
    assert resp.status_code == 409


# ---------------------------------------------------------------------------
# DELETE /appointments/{id}
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_delete_appointment_success(client: AsyncClient):
    mock_uc = AsyncMock(spec=DeleteAppointmentUseCase)
    mock_uc.execute.return_value = None

    with patch(_DECODE_PATH, return_value=_USER_CLAIMS):
        app.dependency_overrides[_get_delete_uc] = lambda: mock_uc
        resp = await client.delete("/api/v1/appointments/appt-1", headers=_AUTH)
    app.dependency_overrides.pop(_get_delete_uc, None)
    assert resp.status_code == 204


# ---------------------------------------------------------------------------
# POST /appointments/{id}/confirm
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_confirm_appointment_success(client: AsyncClient):
    confirmed = _make_appt(status=STATUS_CONFIRMED)
    mock_uc = AsyncMock(spec=ConfirmAppointmentUseCase)
    mock_uc.execute.return_value = confirmed

    with patch(_DECODE_PATH, return_value=_USER_CLAIMS):
        app.dependency_overrides[_get_confirm_uc] = lambda: mock_uc
        resp = await client.post("/api/v1/appointments/appt-1/confirm", headers=_AUTH)
    app.dependency_overrides.pop(_get_confirm_uc, None)
    assert resp.status_code == 200
    assert resp.json()["status"] == STATUS_CONFIRMED


@pytest.mark.anyio
async def test_confirm_already_cancelled_raises(client: AsyncClient):
    mock_uc = AsyncMock(spec=ConfirmAppointmentUseCase)
    mock_uc.execute.side_effect = ConflictException("Transición no permitida")

    with patch(_DECODE_PATH, return_value=_USER_CLAIMS):
        app.dependency_overrides[_get_confirm_uc] = lambda: mock_uc
        resp = await client.post("/api/v1/appointments/appt-1/confirm", headers=_AUTH)
    app.dependency_overrides.pop(_get_confirm_uc, None)
    assert resp.status_code == 409


# ---------------------------------------------------------------------------
# POST /appointments/{id}/cancel
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_cancel_appointment_with_reason(client: AsyncClient):
    cancelled = _make_appt(
        status=STATUS_CANCELLED,
        cancel_reason="Cliente no se presentó",
        cancelled_at=_CREATED,
    )
    mock_uc = AsyncMock(spec=CancelAppointmentUseCase)
    mock_uc.execute.return_value = cancelled

    with patch(_DECODE_PATH, return_value=_USER_CLAIMS):
        app.dependency_overrides[_get_cancel_uc] = lambda: mock_uc
        resp = await client.post(
            "/api/v1/appointments/appt-1/cancel",
            headers=_AUTH,
            json={"reason": "Cliente no se presentó"},
        )
    app.dependency_overrides.pop(_get_cancel_uc, None)
    assert resp.status_code == 200
    assert resp.json()["status"] == STATUS_CANCELLED
    assert resp.json()["cancel_reason"] == "Cliente no se presentó"


# ---------------------------------------------------------------------------
# GET /appointments/availability
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_get_availability_returns_slots(client: AsyncClient):
    mock_uc = AsyncMock(spec=GetAvailabilityUseCase)
    mock_uc.execute.return_value = [
        {"start_at": _START, "end_at": _END, "available": True},
        {
            "start_at": _END,
            "end_at": _END + timedelta(hours=1),
            "available": False,
        },
    ]

    with patch(_DECODE_PATH, return_value=_USER_CLAIMS):
        app.dependency_overrides[_get_availability_uc] = lambda: mock_uc
        resp = await client.get(
            "/api/v1/appointments/availability?date=2026-07-10",
            headers=_AUTH,
        )
    app.dependency_overrides.pop(_get_availability_uc, None)
    assert resp.status_code == 200
    data = resp.json()
    assert data["date"] == "2026-07-10"
    assert len(data["slots"]) == 2
    assert data["slots"][0]["available"] is True
    assert data["slots"][1]["available"] is False


# ---------------------------------------------------------------------------
# Conflict detection — unit test on use case
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_create_detects_conflict():
    repo = MagicMock(spec=AppointmentRepository)
    existing = _make_appt(id="appt-existing")
    repo.find_conflicts.return_value = [existing]

    uc = CreateAppointmentUseCase(repo)

    with pytest.raises(ConflictException, match="superponen"):
        await uc.execute(
            tenant_id="tenant-abc",
            created_by="uid-user",
            appointment_type="appointment",
            title="Test",
            start_at=_START,
            end_at=_END,
            mechanic_id="mech-1",
        )


@pytest.mark.anyio
async def test_create_no_conflict_when_no_mechanic():
    repo = MagicMock(spec=AppointmentRepository)
    new_appt = _make_appt(mechanic_id=None)
    repo.create.return_value = None
    repo.find_by_id.return_value = new_appt

    uc = CreateAppointmentUseCase(repo)
    result = await uc.execute(
        tenant_id="tenant-abc",
        created_by="uid-user",
        appointment_type="reminder",
        title="Recordatorio",
        start_at=_START,
        end_at=_END,
    )
    repo.find_conflicts.assert_not_called()
    assert result.id == "appt-1"
