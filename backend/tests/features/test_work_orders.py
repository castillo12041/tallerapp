"""
Tests del feature de órdenes de trabajo (Fase 12).

Repositorios y use cases se mockean completamente.
Se testea: endpoints CRUD, workflow de estados, bitácora, validaciones.
"""

from __future__ import annotations

import time
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient

from app.core.exceptions import ConflictException, NotFoundException
from app.features.inspections.domain.entities import ClientSnapshot, VehicleSnapshot
from app.features.work_orders.application.use_cases import (
    CreateWorkOrderUseCase,
    GetWorkOrderUseCase,
    ListWorkOrdersUseCase,
    UpdateWorkOrderUseCase,
)
from app.features.work_orders.application.workflow_use_cases import (
    AddEntryUseCase,
    CancelWorkOrderUseCase,
    CompleteWorkOrderUseCase,
    QualityCheckUseCase,
    ResumeWorkOrderUseCase,
    StartWorkOrderUseCase,
    WaitPartsUseCase,
)
from app.features.work_orders.domain.entities import WorkOrder, WorkOrderEntry
from app.features.work_orders.domain.workflow import (
    STATUS_CANCELLED,
    STATUS_COMPLETED,
    STATUS_IN_PROGRESS,
    STATUS_PENDING,
    STATUS_QUALITY_CHECK,
    STATUS_WAITING_PARTS,
    validate_transition,
)
from app.features.work_orders.infrastructure.work_order_repository import WorkOrderRepository
from app.features.work_orders.infrastructure.entry_repository import WorkOrderEntryRepository
from app.features.work_orders.presentation.router import (
    _get_add_entry_uc,
    _get_cancel_uc,
    _get_complete_uc,
    _get_create_uc,
    _get_get_uc,
    _get_list_uc,
    _get_quality_check_uc,
    _get_resume_uc,
    _get_start_uc,
    _get_update_uc,
    _get_wait_parts_uc,
)
from app.main import app

_NOW = int(time.time())
_AUTH_HEADERS = {"Authorization": "Bearer fake-token"}
_DECODE_PATH = "app.dependencies.auth.decode_access_token"

_MANAGER_CLAIMS = {
    "sub": "uid-manager",
    "tenant_id": "tenant-abc",
    "role": "workshopmanager",
    "permissions": [
        "work_orders:read",
        "work_orders:create",
        "work_orders:update",
        "work_orders:complete",
    ],
    "plan": "professional",
    "type": "access",
    "exp": _NOW + 1800,
    "iat": _NOW,
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_wo(status: str = STATUS_PENDING, wo_id: str = "wo-001") -> WorkOrder:
    now = datetime.now(timezone.utc)
    snap = VehicleSnapshot(id="veh-1", plate="ABCD12", make="Toyota", model="Corolla", year=2020)
    return WorkOrder(
        id=wo_id,
        tenant_id="tenant-abc",
        number="OT-2024-000001",
        status=status,
        vehicle_snapshot=snap,
        mechanic_id="uid-manager",
        mechanic_name="Juan Mecánico",
        created_at=now,
        updated_at=now,
        created_by="uid-manager",
        updated_by="uid-manager",
    )


def _make_entry(entry_type: str = "status_change") -> WorkOrderEntry:
    now = datetime.now(timezone.utc)
    return WorkOrderEntry(
        id="entry-001",
        tenant_id="tenant-abc",
        work_order_id="wo-001",
        entry_type=entry_type,
        from_status=STATUS_PENDING if entry_type == "status_change" else None,
        to_status=STATUS_IN_PROGRESS if entry_type == "status_change" else None,
        content="Iniciando trabajo" if entry_type == "note" else None,
        created_at=now,
        created_by="uid-manager",
    )


@pytest.fixture(autouse=True)
def clear_overrides():
    yield
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Domain — workflow
# ---------------------------------------------------------------------------


def test_workflow_valid_transitions() -> None:
    validate_transition(STATUS_PENDING, STATUS_IN_PROGRESS)
    validate_transition(STATUS_IN_PROGRESS, STATUS_WAITING_PARTS)
    validate_transition(STATUS_IN_PROGRESS, STATUS_QUALITY_CHECK)
    validate_transition(STATUS_WAITING_PARTS, STATUS_IN_PROGRESS)
    validate_transition(STATUS_QUALITY_CHECK, STATUS_COMPLETED)
    validate_transition(STATUS_QUALITY_CHECK, STATUS_IN_PROGRESS)
    validate_transition(STATUS_PENDING, STATUS_CANCELLED)
    validate_transition(STATUS_IN_PROGRESS, STATUS_CANCELLED)


def test_workflow_invalid_transitions_raise() -> None:
    with pytest.raises(ConflictException):
        validate_transition(STATUS_PENDING, STATUS_COMPLETED)
    with pytest.raises(ConflictException):
        validate_transition(STATUS_COMPLETED, STATUS_IN_PROGRESS)
    with pytest.raises(ConflictException):
        validate_transition(STATUS_CANCELLED, STATUS_PENDING)
    with pytest.raises(ConflictException):
        validate_transition(STATUS_WAITING_PARTS, STATUS_COMPLETED)


def test_work_order_is_terminal() -> None:
    wo = _make_wo(status=STATUS_COMPLETED)
    assert wo.is_terminal
    wo_cancelled = _make_wo(status=STATUS_CANCELLED)
    assert wo_cancelled.is_terminal
    wo_pending = _make_wo(status=STATUS_PENDING)
    assert not wo_pending.is_terminal


def test_work_order_is_deleted() -> None:
    now = datetime.now(timezone.utc)
    wo = _make_wo()
    deleted = WorkOrder(**{**wo.__dict__, "deleted_at": now})
    assert deleted.is_deleted
    assert not wo.is_deleted


# ---------------------------------------------------------------------------
# POST /api/v1/work-orders
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_work_order_success(client: AsyncClient) -> None:
    mock_uc = AsyncMock(spec=CreateWorkOrderUseCase)
    mock_uc.execute.return_value = _make_wo()
    app.dependency_overrides[_get_create_uc] = lambda: mock_uc

    with patch(_DECODE_PATH, return_value=_MANAGER_CLAIMS):
        async with client as c:
            response = await c.post(
                "/api/v1/work-orders",
                json={"mechanic_id": "uid-manager", "estimate_id": "est-001"},
                headers=_AUTH_HEADERS,
            )

    assert response.status_code == 201
    data = response.json()
    assert data["number"] == "OT-2024-000001"
    assert data["status"] == STATUS_PENDING


@pytest.mark.asyncio
async def test_create_work_order_no_source_rejected(client: AsyncClient) -> None:
    mock_uc = AsyncMock(spec=CreateWorkOrderUseCase)
    mock_uc.execute.side_effect = ConflictException("presupuesto o inspección")
    app.dependency_overrides[_get_create_uc] = lambda: mock_uc

    with patch(_DECODE_PATH, return_value=_MANAGER_CLAIMS):
        async with client as c:
            response = await c.post(
                "/api/v1/work-orders",
                json={"mechanic_id": "uid-manager"},
                headers=_AUTH_HEADERS,
            )

    assert response.status_code == 409


@pytest.mark.asyncio
async def test_create_work_order_no_permission(client: AsyncClient) -> None:
    claims = {**_MANAGER_CLAIMS, "permissions": ["work_orders:read"]}
    with patch(_DECODE_PATH, return_value=claims):
        async with client as c:
            response = await c.post(
                "/api/v1/work-orders",
                json={"mechanic_id": "uid-m"},
                headers=_AUTH_HEADERS,
            )
    assert response.status_code == 403


# ---------------------------------------------------------------------------
# GET /api/v1/work-orders
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_work_orders(client: AsyncClient) -> None:
    mock_uc = AsyncMock(spec=ListWorkOrdersUseCase)
    mock_uc.execute.return_value = [_make_wo(), _make_wo(wo_id="wo-002")]
    app.dependency_overrides[_get_list_uc] = lambda: mock_uc

    with patch(_DECODE_PATH, return_value=_MANAGER_CLAIMS):
        async with client as c:
            response = await c.get("/api/v1/work-orders", headers=_AUTH_HEADERS)

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2


@pytest.mark.asyncio
async def test_list_work_orders_filtered(client: AsyncClient) -> None:
    mock_uc = AsyncMock(spec=ListWorkOrdersUseCase)
    mock_uc.execute.return_value = []
    app.dependency_overrides[_get_list_uc] = lambda: mock_uc

    with patch(_DECODE_PATH, return_value=_MANAGER_CLAIMS):
        async with client as c:
            response = await c.get(
                "/api/v1/work-orders?status=in_progress&mechanic_id=uid-m",
                headers=_AUTH_HEADERS,
            )

    assert response.status_code == 200
    mock_uc.execute.assert_called_once_with(
        tenant_id="tenant-abc",
        status="in_progress",
        mechanic_id="uid-m",
        estimate_id=None,
    )


# ---------------------------------------------------------------------------
# GET /api/v1/work-orders/{id}
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_work_order_with_entries(client: AsyncClient) -> None:
    mock_uc = AsyncMock(spec=GetWorkOrderUseCase)
    mock_uc.execute.return_value = (_make_wo(), [_make_entry()])
    app.dependency_overrides[_get_get_uc] = lambda: mock_uc

    with patch(_DECODE_PATH, return_value=_MANAGER_CLAIMS):
        async with client as c:
            response = await c.get("/api/v1/work-orders/wo-001", headers=_AUTH_HEADERS)

    assert response.status_code == 200
    data = response.json()
    assert len(data["entries"]) == 1
    assert data["entries"][0]["entry_type"] == "status_change"


@pytest.mark.asyncio
async def test_get_work_order_not_found(client: AsyncClient) -> None:
    mock_uc = AsyncMock(spec=GetWorkOrderUseCase)
    mock_uc.execute.side_effect = NotFoundException("no encontrada")
    app.dependency_overrides[_get_get_uc] = lambda: mock_uc

    with patch(_DECODE_PATH, return_value=_MANAGER_CLAIMS):
        async with client as c:
            response = await c.get("/api/v1/work-orders/no-existe", headers=_AUTH_HEADERS)

    assert response.status_code == 404


# ---------------------------------------------------------------------------
# PATCH /api/v1/work-orders/{id}
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_update_work_order_success(client: AsyncClient) -> None:
    mock_uc = AsyncMock(spec=UpdateWorkOrderUseCase)
    mock_uc.execute.return_value = _make_wo()
    app.dependency_overrides[_get_update_uc] = lambda: mock_uc

    with patch(_DECODE_PATH, return_value=_MANAGER_CLAIMS):
        async with client as c:
            response = await c.patch(
                "/api/v1/work-orders/wo-001",
                json={"diagnosis": "Problema en frenos"},
                headers=_AUTH_HEADERS,
            )

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_update_terminal_work_order_rejected(client: AsyncClient) -> None:
    mock_uc = AsyncMock(spec=UpdateWorkOrderUseCase)
    mock_uc.execute.side_effect = ConflictException("OT en estado completed")
    app.dependency_overrides[_get_update_uc] = lambda: mock_uc

    with patch(_DECODE_PATH, return_value=_MANAGER_CLAIMS):
        async with client as c:
            response = await c.patch(
                "/api/v1/work-orders/wo-001",
                json={"notes": "x"},
                headers=_AUTH_HEADERS,
            )

    assert response.status_code == 409


# ---------------------------------------------------------------------------
# Workflow endpoints
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_start_work_order(client: AsyncClient) -> None:
    mock_uc = AsyncMock(spec=StartWorkOrderUseCase)
    mock_uc.execute.return_value = None
    app.dependency_overrides[_get_start_uc] = lambda: mock_uc

    with patch(_DECODE_PATH, return_value=_MANAGER_CLAIMS):
        async with client as c:
            response = await c.post("/api/v1/work-orders/wo-001/start", headers=_AUTH_HEADERS)

    assert response.status_code == 204


@pytest.mark.asyncio
async def test_start_already_started_rejected(client: AsyncClient) -> None:
    mock_uc = AsyncMock(spec=StartWorkOrderUseCase)
    mock_uc.execute.side_effect = ConflictException("Transición no permitida")
    app.dependency_overrides[_get_start_uc] = lambda: mock_uc

    with patch(_DECODE_PATH, return_value=_MANAGER_CLAIMS):
        async with client as c:
            response = await c.post("/api/v1/work-orders/wo-001/start", headers=_AUTH_HEADERS)

    assert response.status_code == 409


@pytest.mark.asyncio
async def test_wait_parts(client: AsyncClient) -> None:
    mock_uc = AsyncMock(spec=WaitPartsUseCase)
    mock_uc.execute.return_value = None
    app.dependency_overrides[_get_wait_parts_uc] = lambda: mock_uc

    with patch(_DECODE_PATH, return_value=_MANAGER_CLAIMS):
        async with client as c:
            response = await c.post(
                "/api/v1/work-orders/wo-001/wait-parts",
                json={"note": "Falta el filtro"},
                headers=_AUTH_HEADERS,
            )

    assert response.status_code == 204


@pytest.mark.asyncio
async def test_resume_work_order(client: AsyncClient) -> None:
    mock_uc = AsyncMock(spec=ResumeWorkOrderUseCase)
    mock_uc.execute.return_value = None
    app.dependency_overrides[_get_resume_uc] = lambda: mock_uc

    with patch(_DECODE_PATH, return_value=_MANAGER_CLAIMS):
        async with client as c:
            response = await c.post("/api/v1/work-orders/wo-001/resume", headers=_AUTH_HEADERS)

    assert response.status_code == 204


@pytest.mark.asyncio
async def test_quality_check(client: AsyncClient) -> None:
    mock_uc = AsyncMock(spec=QualityCheckUseCase)
    mock_uc.execute.return_value = None
    app.dependency_overrides[_get_quality_check_uc] = lambda: mock_uc

    with patch(_DECODE_PATH, return_value=_MANAGER_CLAIMS):
        async with client as c:
            response = await c.post(
                "/api/v1/work-orders/wo-001/quality-check", headers=_AUTH_HEADERS
            )

    assert response.status_code == 204


@pytest.mark.asyncio
async def test_complete_work_order(client: AsyncClient) -> None:
    mock_uc = AsyncMock(spec=CompleteWorkOrderUseCase)
    mock_uc.execute.return_value = None
    app.dependency_overrides[_get_complete_uc] = lambda: mock_uc

    with patch(_DECODE_PATH, return_value=_MANAGER_CLAIMS):
        async with client as c:
            response = await c.post("/api/v1/work-orders/wo-001/complete", headers=_AUTH_HEADERS)

    assert response.status_code == 204


@pytest.mark.asyncio
async def test_complete_requires_complete_permission(client: AsyncClient) -> None:
    claims = {**_MANAGER_CLAIMS, "permissions": ["work_orders:update"]}
    with patch(_DECODE_PATH, return_value=claims):
        async with client as c:
            response = await c.post("/api/v1/work-orders/wo-001/complete", headers=_AUTH_HEADERS)
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_cancel_work_order(client: AsyncClient) -> None:
    mock_uc = AsyncMock(spec=CancelWorkOrderUseCase)
    mock_uc.execute.return_value = None
    app.dependency_overrides[_get_cancel_uc] = lambda: mock_uc

    with patch(_DECODE_PATH, return_value=_MANAGER_CLAIMS):
        async with client as c:
            response = await c.post(
                "/api/v1/work-orders/wo-001/cancel",
                json={"reason": "Cliente canceló el servicio"},
                headers=_AUTH_HEADERS,
            )

    assert response.status_code == 204


@pytest.mark.asyncio
async def test_cancel_completed_rejected(client: AsyncClient) -> None:
    mock_uc = AsyncMock(spec=CancelWorkOrderUseCase)
    mock_uc.execute.side_effect = ConflictException("Transición no permitida")
    app.dependency_overrides[_get_cancel_uc] = lambda: mock_uc

    with patch(_DECODE_PATH, return_value=_MANAGER_CLAIMS):
        async with client as c:
            response = await c.post(
                "/api/v1/work-orders/wo-001/cancel",
                json={},
                headers=_AUTH_HEADERS,
            )

    assert response.status_code == 409


@pytest.mark.asyncio
async def test_add_entry(client: AsyncClient) -> None:
    mock_uc = AsyncMock(spec=AddEntryUseCase)
    mock_uc.execute.return_value = None
    app.dependency_overrides[_get_add_entry_uc] = lambda: mock_uc

    with patch(_DECODE_PATH, return_value=_MANAGER_CLAIMS):
        async with client as c:
            response = await c.post(
                "/api/v1/work-orders/wo-001/entries",
                json={"content": "Se reemplazó el aceite de motor"},
                headers=_AUTH_HEADERS,
            )

    assert response.status_code == 201


@pytest.mark.asyncio
async def test_add_entry_empty_content_rejected(client: AsyncClient) -> None:
    with patch(_DECODE_PATH, return_value=_MANAGER_CLAIMS):
        async with client as c:
            response = await c.post(
                "/api/v1/work-orders/wo-001/entries",
                json={"content": ""},
                headers=_AUTH_HEADERS,
            )
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# Use case unit tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_start_use_case_rejects_completed() -> None:
    wo = _make_wo(status=STATUS_COMPLETED)
    mock_repo = MagicMock(spec=WorkOrderRepository)
    mock_repo.find_by_id.return_value = wo
    uc = StartWorkOrderUseCase(mock_repo, MagicMock(spec=WorkOrderEntryRepository))

    with pytest.raises(ConflictException):
        await uc.execute("tenant-abc", "wo-001", "uid")


@pytest.mark.asyncio
async def test_complete_use_case_requires_quality_check() -> None:
    wo = _make_wo(status=STATUS_IN_PROGRESS)
    mock_repo = MagicMock(spec=WorkOrderRepository)
    mock_repo.find_by_id.return_value = wo
    uc = CompleteWorkOrderUseCase(mock_repo, MagicMock(spec=WorkOrderEntryRepository))

    with pytest.raises(ConflictException):
        await uc.execute("tenant-abc", "wo-001", "uid")


@pytest.mark.asyncio
async def test_update_use_case_rejects_terminal() -> None:
    wo = _make_wo(status=STATUS_CANCELLED)
    mock_repo = MagicMock(spec=WorkOrderRepository)
    mock_repo.find_by_id.return_value = wo
    uc = UpdateWorkOrderUseCase(mock_repo)

    with pytest.raises(ConflictException):
        await uc.execute("tenant-abc", "wo-001", "uid", {"notes": "x"})


@pytest.mark.asyncio
async def test_add_entry_not_found() -> None:
    mock_repo = MagicMock(spec=WorkOrderRepository)
    mock_repo.find_by_id.return_value = None
    uc = AddEntryUseCase(mock_repo, MagicMock(spec=WorkOrderEntryRepository))

    with pytest.raises(NotFoundException):
        await uc.execute("tenant-abc", "no-existe", "nota", "uid")


@pytest.mark.asyncio
async def test_cancel_use_case_records_reason() -> None:
    wo = _make_wo(status=STATUS_IN_PROGRESS)
    mock_repo = MagicMock(spec=WorkOrderRepository)
    mock_repo.find_by_id.return_value = wo
    mock_repo.update.return_value = None

    mock_entry_repo = MagicMock(spec=WorkOrderEntryRepository)
    mock_entry_repo.add.return_value = None

    uc = CancelWorkOrderUseCase(mock_repo, mock_entry_repo)
    await uc.execute("tenant-abc", "wo-001", "uid", reason="Motivo de cancelación")

    call_args = mock_entry_repo.add.call_args[0]
    entry_dict = call_args[1]
    assert entry_dict["content"] == "Motivo de cancelación"
    assert entry_dict["toStatus"] == STATUS_CANCELLED
