"""
Tests del feature de inspecciones.
"""

from __future__ import annotations

import time
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient

from app.core.exceptions import ConflictException, NotFoundException
from app.features.inspections.application.use_cases import (
    CreateInspectionUseCase,
    GetInspectionUseCase,
    ListInspectionsUseCase,
)
from app.features.inspections.application.workflow_use_cases import (
    CancelInspectionUseCase,
    CompleteInspectionUseCase,
    ReopenInspectionUseCase,
    StartInspectionUseCase,
    SubmitInspectionUseCase,
    UpdateItemUseCase,
)
from app.features.inspections.domain.entities import (
    Inspection,
    InspectionItem,
    VehicleSnapshot,
)
from app.features.inspections.domain.workflow import (
    compute_score,
    validate_transition,
)
from app.features.inspections.presentation.router import (
    _get_cancel_uc,
    _get_complete_uc,
    _get_create_uc,
    _get_get_uc,
    _get_list_uc,
    _get_reopen_uc,
    _get_start_uc,
    _get_submit_uc,
    _get_update_item_uc,
)
from app.main import app

_NOW = int(time.time())
_AUTH_HEADERS = {"Authorization": "Bearer fake-token"}
_DECODE_PATH = "app.dependencies.auth.decode_access_token"

_INSPECTOR_CLAIMS = {
    "sub": "uid-inspector",
    "tenant_id": "tenant-abc",
    "role": "inspector",
    "permissions": [
        "inspections:read", "inspections:create",
        "inspections:update", "inspections:complete",
    ],
    "plan": "professional",
    "type": "access",
    "exp": _NOW + 1800,
    "iat": _NOW,
}

_MANAGER_CLAIMS = {
    **_INSPECTOR_CLAIMS,
    "role": "workshopmanager",
    "permissions": [
        "inspections:read", "inspections:create", "inspections:update",
        "inspections:complete", "inspections:review",
    ],
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_inspection(status: str = "draft") -> Inspection:
    now = datetime.now(timezone.utc)
    snap = VehicleSnapshot(id="veh-1", plate="ABCD12", make="Toyota", model="Corolla")
    return Inspection(
        id="ins-001",
        tenant_id="tenant-abc",
        number="INS-2024-000001",
        vehicle_id="veh-1",
        mechanic_id="uid-inspector",
        status=status,
        vehicle_snapshot=snap,
        total_items=3,
        good_items=2,
        regular_items=1,
        bad_items=0,
        na_items=0,
        total_repair_cost=0.0,
        currency="CLP",
        is_offline=False,
        created_at=now, updated_at=now,
        created_by="uid-inspector", updated_by="uid-inspector",
    )


def _make_item(status: str = "pending") -> InspectionItem:
    now = datetime.now(timezone.utc)
    return InspectionItem(
        id="item-001", tenant_id="tenant-abc", inspection_id="ins-001",
        category="Motor", category_order=1, name="Motor arranca", order=1,
        status=status, photo_urls=(), photo_count=0, is_offline=False,
        created_at=now, updated_at=now, created_by="uid-inspector", updated_by="uid-inspector",
    )


@pytest.fixture(autouse=True)
def clear_overrides():
    yield
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# POST /inspections
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_inspection_success(client: AsyncClient) -> None:
    mock_uc = AsyncMock(spec=CreateInspectionUseCase)
    mock_uc.execute.return_value = _make_inspection()
    app.dependency_overrides[_get_create_uc] = lambda: mock_uc

    with patch(_DECODE_PATH, return_value=_INSPECTOR_CLAIMS):
        async with client as c:
            response = await c.post(
                "/api/v1/inspections/",
                json={"vehicle_id": "veh-1", "mechanic_id": "uid-inspector"},
                headers=_AUTH_HEADERS,
            )

    assert response.status_code == 201
    data = response.json()
    assert data["number"] == "INS-2024-000001"
    assert data["status"] == "draft"
    mock_uc.execute.assert_called_once()


@pytest.mark.asyncio
async def test_create_inspection_missing_required(client: AsyncClient) -> None:
    with patch(_DECODE_PATH, return_value=_INSPECTOR_CLAIMS):
        async with client as c:
            response = await c.post(
                "/api/v1/inspections/",
                json={"vehicle_id": "veh-1"},
                headers=_AUTH_HEADERS,
            )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_inspection_no_permission(client: AsyncClient) -> None:
    with patch(_DECODE_PATH, return_value={**_INSPECTOR_CLAIMS, "permissions": []}):
        async with client as c:
            response = await c.post(
                "/api/v1/inspections/",
                json={"vehicle_id": "veh-1", "mechanic_id": "uid-inspector"},
                headers=_AUTH_HEADERS,
            )

    assert response.status_code == 403


# ---------------------------------------------------------------------------
# GET /inspections
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_inspections_success(client: AsyncClient) -> None:
    mock_uc = AsyncMock(spec=ListInspectionsUseCase)
    mock_uc.execute.return_value = [_make_inspection("draft"), _make_inspection("in_progress")]
    app.dependency_overrides[_get_list_uc] = lambda: mock_uc

    with patch(_DECODE_PATH, return_value=_INSPECTOR_CLAIMS):
        async with client as c:
            response = await c.get("/api/v1/inspections/", headers=_AUTH_HEADERS)

    assert response.status_code == 200
    assert len(response.json()) == 2


@pytest.mark.asyncio
async def test_list_inspections_with_status_filter(client: AsyncClient) -> None:
    mock_uc = AsyncMock(spec=ListInspectionsUseCase)
    mock_uc.execute.return_value = [_make_inspection("in_progress")]
    app.dependency_overrides[_get_list_uc] = lambda: mock_uc

    with patch(_DECODE_PATH, return_value=_INSPECTOR_CLAIMS):
        async with client as c:
            response = await c.get(
                "/api/v1/inspections/?status=in_progress", headers=_AUTH_HEADERS
            )

    assert response.status_code == 200
    mock_uc.execute.assert_called_once_with(
        "tenant-abc", status="in_progress", vehicle_id=None, mechanic_id=None
    )


# ---------------------------------------------------------------------------
# GET /inspections/{id}
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_inspection_success(client: AsyncClient) -> None:
    mock_uc = AsyncMock(spec=GetInspectionUseCase)
    mock_uc.execute.return_value = (_make_inspection(), [_make_item()])
    app.dependency_overrides[_get_get_uc] = lambda: mock_uc

    with patch(_DECODE_PATH, return_value=_INSPECTOR_CLAIMS):
        async with client as c:
            response = await c.get("/api/v1/inspections/ins-001", headers=_AUTH_HEADERS)

    assert response.status_code == 200
    data = response.json()
    assert data["items"] is not None
    assert len(data["items"]) == 1


@pytest.mark.asyncio
async def test_get_inspection_not_found(client: AsyncClient) -> None:
    mock_uc = AsyncMock(spec=GetInspectionUseCase)
    mock_uc.execute.side_effect = NotFoundException("Inspección no encontrada")
    app.dependency_overrides[_get_get_uc] = lambda: mock_uc

    with patch(_DECODE_PATH, return_value=_INSPECTOR_CLAIMS):
        async with client as c:
            response = await c.get("/api/v1/inspections/no-existe", headers=_AUTH_HEADERS)

    assert response.status_code == 404


# ---------------------------------------------------------------------------
# POST /inspections/{id}/start
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_start_inspection_success(client: AsyncClient) -> None:
    mock_uc = AsyncMock(spec=StartInspectionUseCase)
    mock_uc.execute.return_value = _make_inspection("in_progress")
    app.dependency_overrides[_get_start_uc] = lambda: mock_uc

    with patch(_DECODE_PATH, return_value=_INSPECTOR_CLAIMS):
        async with client as c:
            response = await c.post("/api/v1/inspections/ins-001/start", headers=_AUTH_HEADERS)

    assert response.status_code == 200
    assert response.json()["status"] == "in_progress"


@pytest.mark.asyncio
async def test_start_inspection_invalid_transition(client: AsyncClient) -> None:
    mock_uc = AsyncMock(spec=StartInspectionUseCase)
    mock_uc.execute.side_effect = ConflictException("Transición no permitida")
    app.dependency_overrides[_get_start_uc] = lambda: mock_uc

    with patch(_DECODE_PATH, return_value=_INSPECTOR_CLAIMS):
        async with client as c:
            response = await c.post("/api/v1/inspections/ins-001/start", headers=_AUTH_HEADERS)

    assert response.status_code == 409


# ---------------------------------------------------------------------------
# PATCH /inspections/{id}/items/{item_id}
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_update_item_success(client: AsyncClient) -> None:
    mock_uc = AsyncMock(spec=UpdateItemUseCase)
    mock_uc.execute.return_value = _make_item("good")
    app.dependency_overrides[_get_update_item_uc] = lambda: mock_uc

    with patch(_DECODE_PATH, return_value=_INSPECTOR_CLAIMS):
        async with client as c:
            response = await c.patch(
                "/api/v1/inspections/ins-001/items/item-001",
                json={"status": "good"},
                headers=_AUTH_HEADERS,
            )

    assert response.status_code == 200
    assert response.json()["status"] == "good"


# ---------------------------------------------------------------------------
# Workflow endpoints (submit, complete, reopen, cancel)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_submit_inspection_success(client: AsyncClient) -> None:
    mock_uc = AsyncMock(spec=SubmitInspectionUseCase)
    mock_uc.execute.return_value = _make_inspection("review")
    app.dependency_overrides[_get_submit_uc] = lambda: mock_uc

    with patch(_DECODE_PATH, return_value=_INSPECTOR_CLAIMS):
        async with client as c:
            response = await c.post("/api/v1/inspections/ins-001/submit", headers=_AUTH_HEADERS)

    assert response.status_code == 200
    assert response.json()["status"] == "review"


@pytest.mark.asyncio
async def test_complete_inspection_success(client: AsyncClient) -> None:
    mock_uc = AsyncMock(spec=CompleteInspectionUseCase)
    completed = _make_inspection("completed")
    mock_uc.execute.return_value = completed
    app.dependency_overrides[_get_complete_uc] = lambda: mock_uc

    with patch(_DECODE_PATH, return_value=_INSPECTOR_CLAIMS):
        async with client as c:
            response = await c.post(
                "/api/v1/inspections/ins-001/complete", headers=_AUTH_HEADERS
            )

    assert response.status_code == 200
    assert response.json()["status"] == "completed"


@pytest.mark.asyncio
async def test_reopen_inspection_success(client: AsyncClient) -> None:
    mock_uc = AsyncMock(spec=ReopenInspectionUseCase)
    mock_uc.execute.return_value = _make_inspection("in_progress")
    app.dependency_overrides[_get_reopen_uc] = lambda: mock_uc

    with patch(_DECODE_PATH, return_value=_MANAGER_CLAIMS):
        async with client as c:
            response = await c.post(
                "/api/v1/inspections/ins-001/reopen", headers=_AUTH_HEADERS
            )

    assert response.status_code == 200
    assert response.json()["status"] == "in_progress"


@pytest.mark.asyncio
async def test_cancel_inspection_success(client: AsyncClient) -> None:
    mock_uc = AsyncMock(spec=CancelInspectionUseCase)
    mock_uc.execute.return_value = _make_inspection("cancelled")
    app.dependency_overrides[_get_cancel_uc] = lambda: mock_uc

    with patch(_DECODE_PATH, return_value=_MANAGER_CLAIMS):
        async with client as c:
            response = await c.post(
                "/api/v1/inspections/ins-001/cancel", headers=_AUTH_HEADERS
            )

    assert response.status_code == 200
    assert response.json()["status"] == "cancelled"


# ---------------------------------------------------------------------------
# Workflow domain tests
# ---------------------------------------------------------------------------


def test_validate_transition_draft_to_in_progress() -> None:
    validate_transition("draft", "in_progress")  # should not raise


def test_validate_transition_draft_to_completed_raises() -> None:
    from app.core.exceptions import ConflictException
    with pytest.raises(ConflictException):
        validate_transition("draft", "completed")


def test_validate_transition_completed_is_terminal() -> None:
    from app.core.exceptions import ConflictException
    with pytest.raises(ConflictException):
        validate_transition("completed", "in_progress")


def test_compute_score_all_good() -> None:
    score = compute_score(good=10, regular=0, bad=0, na=0, total=10)
    assert score == 100.0


def test_compute_score_mixed() -> None:
    # 5 good (500) + 5 regular (250) = 750 / 1000 = 75.0
    score = compute_score(good=5, regular=5, bad=0, na=0, total=10)
    assert score == 75.0


def test_compute_score_all_bad() -> None:
    score = compute_score(good=0, regular=0, bad=10, na=0, total=10)
    assert score == 0.0


def test_compute_score_all_na_returns_none() -> None:
    score = compute_score(good=0, regular=0, bad=0, na=5, total=5)
    assert score is None


# ---------------------------------------------------------------------------
# Inspection entity tests
# ---------------------------------------------------------------------------


def test_inspection_is_deleted_when_deleted_at_set() -> None:
    now = datetime.now(timezone.utc)
    i = _make_inspection()
    i2 = Inspection(**{**i.__dataclass_fields__, **{k: getattr(i, k) for k in i.__dataclass_fields__}, "deleted_at": now})
    assert i2.is_deleted


def test_inspection_active_not_deleted() -> None:
    assert not _make_inspection().is_deleted
