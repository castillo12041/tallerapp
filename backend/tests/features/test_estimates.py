"""
Tests del feature de presupuestos (Fase 11).

Los repositorios y use cases se mockean completamente.
Se testea: endpoints CRUD, workflow de estados, portal público, validaciones.
"""

from __future__ import annotations

import time
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient

from app.core.exceptions import ConflictException, NotFoundException
from app.features.estimates.application.use_cases import (
    CreateEstimateUseCase,
    DeleteEstimateUseCase,
    GetEstimateUseCase,
    ListEstimatesUseCase,
    UpdateEstimateUseCase,
)
from app.features.estimates.application.workflow_use_cases import (
    AddEstimateItemUseCase,
    RemoveEstimateItemUseCase,
    SendEstimateUseCase,
    ConvertEstimateUseCase,
)
from app.features.estimates.domain.entities import Estimate, EstimateItem
from app.features.estimates.domain.workflow import (
    STATUS_ACCEPTED,
    STATUS_CONVERTED,
    STATUS_DRAFT,
    STATUS_REJECTED,
    STATUS_SENT,
    STATUS_VIEWED,
    validate_transition,
)
from app.features.estimates.presentation.router import (
    _get_add_item_uc,
    _get_convert_uc,
    _get_create_uc,
    _get_delete_uc,
    _get_estimate_repo,
    _get_get_uc,
    _get_item_repo,
    _get_list_uc,
    _get_remove_item_uc,
    _get_send_uc,
    _get_token_repo,
    _get_update_uc,
)
from app.features.estimates.infrastructure.estimate_repository import EstimateRepository
from app.features.estimates.infrastructure.item_repository import EstimateItemRepository
from app.features.inspections.domain.entities import ClientSnapshot, VehicleSnapshot
from app.features.qr.infrastructure.hmac_signer import encode_token
from app.features.qr.infrastructure.public_token_repository import PublicTokenRepository
from app.features.qr.domain.entities import PublicToken
from app.main import app

_NOW = int(time.time())
_AUTH_HEADERS = {"Authorization": "Bearer fake-token"}
_DECODE_PATH = "app.dependencies.auth.decode_access_token"
_SECRET = "test-hmac-secret-key-32-characters!!"

_MANAGER_CLAIMS = {
    "sub": "uid-manager",
    "tenant_id": "tenant-abc",
    "role": "workshopmanager",
    "permissions": ["estimates:read", "estimates:write"],
    "plan": "professional",
    "type": "access",
    "exp": _NOW + 1800,
    "iat": _NOW,
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_vehicle_snap() -> VehicleSnapshot:
    return VehicleSnapshot(id="veh-1", plate="ABCD12", make="Toyota", model="Corolla", year=2020)


def _make_estimate(status: str = STATUS_DRAFT, estimate_id: str = "est-001") -> Estimate:
    now = datetime.now(timezone.utc)
    return Estimate(
        id=estimate_id,
        tenant_id="tenant-abc",
        number="EST-2024-000001",
        status=status,
        vehicle_snapshot=_make_vehicle_snap(),
        items_count=2,
        subtotal=100_000.0,
        tax_rate=0.19,
        tax_amount=19_000.0,
        total=119_000.0,
        currency="CLP",
        notes="Revisión completa",
        created_at=now,
        updated_at=now,
        created_by="uid-manager",
        updated_by="uid-manager",
    )


def _make_item(item_id: str = "item-001") -> EstimateItem:
    now = datetime.now(timezone.utc)
    return EstimateItem(
        id=item_id,
        tenant_id="tenant-abc",
        estimate_id="est-001",
        name="Cambio de aceite",
        quantity=1.0,
        unit_price=50_000.0,
        subtotal=50_000.0,
        created_at=now,
        updated_at=now,
        created_by="uid-manager",
        updated_by="uid-manager",
    )


def _make_public_token(estimate_id: str = "est-001", revoked: bool = False) -> PublicToken:
    now = datetime.now(timezone.utc)
    return PublicToken(
        id="tok-001",
        tenant_id="tenant-abc",
        resource_id=estimate_id,
        token_type="budget_access",
        issued_at=now,
        expires_at=now + timedelta(days=30),
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
# Domain — workflow
# ---------------------------------------------------------------------------


def test_workflow_valid_transitions() -> None:
    validate_transition(STATUS_DRAFT, STATUS_SENT)
    validate_transition(STATUS_SENT, STATUS_VIEWED)
    validate_transition(STATUS_VIEWED, STATUS_ACCEPTED)
    validate_transition(STATUS_VIEWED, STATUS_REJECTED)
    validate_transition(STATUS_ACCEPTED, STATUS_CONVERTED)


def test_workflow_invalid_transition_raises() -> None:
    with pytest.raises(ConflictException):
        validate_transition(STATUS_DRAFT, STATUS_ACCEPTED)
    with pytest.raises(ConflictException):
        validate_transition(STATUS_CONVERTED, STATUS_DRAFT)
    with pytest.raises(ConflictException):
        validate_transition(STATUS_REJECTED, STATUS_ACCEPTED)


def test_estimate_is_deleted() -> None:
    now = datetime.now(timezone.utc)
    est = _make_estimate()
    deleted = Estimate(**{**est.__dict__, "deleted_at": now})
    assert deleted.is_deleted
    assert not est.is_deleted


# ---------------------------------------------------------------------------
# POST /api/v1/estimates
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_estimate_success(client: AsyncClient) -> None:
    mock_uc = AsyncMock(spec=CreateEstimateUseCase)
    estimate = _make_estimate()
    mock_uc.execute.return_value = estimate
    app.dependency_overrides[_get_create_uc] = lambda: mock_uc
    app.dependency_overrides[_get_item_repo] = lambda: _mock_item_repo([_make_item()])

    with patch(_DECODE_PATH, return_value=_MANAGER_CLAIMS):
        async with client as c:
            response = await c.post(
                "/api/v1/estimates",
                json={
                    "vehicle_id": "veh-1",
                    "items": [{"name": "Cambio aceite", "quantity": 1, "unit_price": 50000}],
                },
                headers=_AUTH_HEADERS,
            )

    assert response.status_code == 201
    data = response.json()
    assert data["number"] == "EST-2024-000001"
    assert data["status"] == STATUS_DRAFT
    assert "items" in data


@pytest.mark.asyncio
async def test_create_estimate_missing_items_rejected(client: AsyncClient) -> None:
    mock_uc = AsyncMock(spec=CreateEstimateUseCase)
    mock_uc.execute.side_effect = ConflictException("al menos un ítem")
    app.dependency_overrides[_get_create_uc] = lambda: mock_uc
    app.dependency_overrides[_get_item_repo] = lambda: _mock_item_repo([])

    with patch(_DECODE_PATH, return_value=_MANAGER_CLAIMS):
        async with client as c:
            response = await c.post(
                "/api/v1/estimates",
                json={"vehicle_id": "veh-1", "items": []},
                headers=_AUTH_HEADERS,
            )

    assert response.status_code in {409, 422}


@pytest.mark.asyncio
async def test_create_estimate_no_permission(client: AsyncClient) -> None:
    claims = {**_MANAGER_CLAIMS, "permissions": ["estimates:read"]}
    with patch(_DECODE_PATH, return_value=claims):
        async with client as c:
            response = await c.post(
                "/api/v1/estimates",
                json={"vehicle_id": "v", "items": [{"name": "x", "quantity": 1, "unit_price": 1}]},
                headers=_AUTH_HEADERS,
            )
    assert response.status_code == 403


# ---------------------------------------------------------------------------
# GET /api/v1/estimates
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_estimates(client: AsyncClient) -> None:
    mock_uc = AsyncMock(spec=ListEstimatesUseCase)
    mock_uc.execute.return_value = [_make_estimate()]
    app.dependency_overrides[_get_list_uc] = lambda: mock_uc

    with patch(_DECODE_PATH, return_value=_MANAGER_CLAIMS):
        async with client as c:
            response = await c.get("/api/v1/estimates", headers=_AUTH_HEADERS)

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["number"] == "EST-2024-000001"


@pytest.mark.asyncio
async def test_list_estimates_filtered_by_status(client: AsyncClient) -> None:
    mock_uc = AsyncMock(spec=ListEstimatesUseCase)
    mock_uc.execute.return_value = []
    app.dependency_overrides[_get_list_uc] = lambda: mock_uc

    with patch(_DECODE_PATH, return_value=_MANAGER_CLAIMS):
        async with client as c:
            response = await c.get(
                "/api/v1/estimates?status=sent", headers=_AUTH_HEADERS
            )

    assert response.status_code == 200
    mock_uc.execute.assert_called_once_with(
        tenant_id="tenant-abc", status="sent", inspection_id=None
    )


# ---------------------------------------------------------------------------
# GET /api/v1/estimates/{id}
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_estimate_success(client: AsyncClient) -> None:
    mock_uc = AsyncMock(spec=GetEstimateUseCase)
    mock_uc.execute.return_value = (_make_estimate(), [_make_item()])
    app.dependency_overrides[_get_get_uc] = lambda: mock_uc

    with patch(_DECODE_PATH, return_value=_MANAGER_CLAIMS):
        async with client as c:
            response = await c.get("/api/v1/estimates/est-001", headers=_AUTH_HEADERS)

    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 1


@pytest.mark.asyncio
async def test_get_estimate_not_found(client: AsyncClient) -> None:
    mock_uc = AsyncMock(spec=GetEstimateUseCase)
    mock_uc.execute.side_effect = NotFoundException("no encontrado")
    app.dependency_overrides[_get_get_uc] = lambda: mock_uc

    with patch(_DECODE_PATH, return_value=_MANAGER_CLAIMS):
        async with client as c:
            response = await c.get("/api/v1/estimates/no-existe", headers=_AUTH_HEADERS)

    assert response.status_code == 404


# ---------------------------------------------------------------------------
# PATCH /api/v1/estimates/{id}
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_update_estimate_draft_allowed(client: AsyncClient) -> None:
    mock_uc = AsyncMock(spec=UpdateEstimateUseCase)
    mock_uc.execute.return_value = _make_estimate()
    app.dependency_overrides[_get_update_uc] = lambda: mock_uc

    with patch(_DECODE_PATH, return_value=_MANAGER_CLAIMS):
        async with client as c:
            response = await c.patch(
                "/api/v1/estimates/est-001",
                json={"notes": "Nueva nota"},
                headers=_AUTH_HEADERS,
            )

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_update_estimate_non_draft_rejected(client: AsyncClient) -> None:
    mock_uc = AsyncMock(spec=UpdateEstimateUseCase)
    mock_uc.execute.side_effect = ConflictException("solo en estado draft")
    app.dependency_overrides[_get_update_uc] = lambda: mock_uc

    with patch(_DECODE_PATH, return_value=_MANAGER_CLAIMS):
        async with client as c:
            response = await c.patch(
                "/api/v1/estimates/est-001",
                json={"notes": "x"},
                headers=_AUTH_HEADERS,
            )

    assert response.status_code == 409


# ---------------------------------------------------------------------------
# DELETE /api/v1/estimates/{id}
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_delete_estimate_draft(client: AsyncClient) -> None:
    mock_uc = AsyncMock(spec=DeleteEstimateUseCase)
    mock_uc.execute.return_value = None
    app.dependency_overrides[_get_delete_uc] = lambda: mock_uc

    with patch(_DECODE_PATH, return_value=_MANAGER_CLAIMS):
        async with client as c:
            response = await c.delete("/api/v1/estimates/est-001", headers=_AUTH_HEADERS)

    assert response.status_code == 204


@pytest.mark.asyncio
async def test_delete_estimate_non_draft_rejected(client: AsyncClient) -> None:
    mock_uc = AsyncMock(spec=DeleteEstimateUseCase)
    mock_uc.execute.side_effect = ConflictException("solo en estado draft")
    app.dependency_overrides[_get_delete_uc] = lambda: mock_uc

    with patch(_DECODE_PATH, return_value=_MANAGER_CLAIMS):
        async with client as c:
            response = await c.delete("/api/v1/estimates/est-001", headers=_AUTH_HEADERS)

    assert response.status_code == 409


# ---------------------------------------------------------------------------
# POST /api/v1/estimates/{id}/items
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_add_item_success(client: AsyncClient) -> None:
    mock_uc = AsyncMock(spec=AddEstimateItemUseCase)
    mock_uc.execute.return_value = None
    app.dependency_overrides[_get_add_item_uc] = lambda: mock_uc

    with patch(_DECODE_PATH, return_value=_MANAGER_CLAIMS):
        async with client as c:
            response = await c.post(
                "/api/v1/estimates/est-001/items",
                json={"name": "Filtro aceite", "quantity": 1, "unit_price": 15000},
                headers=_AUTH_HEADERS,
            )

    assert response.status_code == 201


@pytest.mark.asyncio
async def test_add_item_non_draft_rejected(client: AsyncClient) -> None:
    mock_uc = AsyncMock(spec=AddEstimateItemUseCase)
    mock_uc.execute.side_effect = ConflictException("solo en estado draft")
    app.dependency_overrides[_get_add_item_uc] = lambda: mock_uc

    with patch(_DECODE_PATH, return_value=_MANAGER_CLAIMS):
        async with client as c:
            response = await c.post(
                "/api/v1/estimates/est-001/items",
                json={"name": "x", "quantity": 1, "unit_price": 1},
                headers=_AUTH_HEADERS,
            )

    assert response.status_code == 409


# ---------------------------------------------------------------------------
# DELETE /api/v1/estimates/{id}/items/{item_id}
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_remove_item_success(client: AsyncClient) -> None:
    mock_uc = AsyncMock(spec=RemoveEstimateItemUseCase)
    mock_uc.execute.return_value = None
    app.dependency_overrides[_get_remove_item_uc] = lambda: mock_uc

    with patch(_DECODE_PATH, return_value=_MANAGER_CLAIMS):
        async with client as c:
            response = await c.delete(
                "/api/v1/estimates/est-001/items/item-001", headers=_AUTH_HEADERS
            )

    assert response.status_code == 204


# ---------------------------------------------------------------------------
# POST /api/v1/estimates/{id}/send
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_send_estimate_success(client: AsyncClient) -> None:
    mock_uc = AsyncMock(spec=SendEstimateUseCase)
    mock_uc.execute.return_value = "https://example.com/api/v1/public/estimates/tok123"
    app.dependency_overrides[_get_send_uc] = lambda: mock_uc

    with patch(_DECODE_PATH, return_value=_MANAGER_CLAIMS):
        async with client as c:
            response = await c.post("/api/v1/estimates/est-001/send", headers=_AUTH_HEADERS)

    assert response.status_code == 200
    data = response.json()
    assert "public_url" in data
    assert "tok123" in data["public_url"]


@pytest.mark.asyncio
async def test_send_estimate_wrong_status(client: AsyncClient) -> None:
    mock_uc = AsyncMock(spec=SendEstimateUseCase)
    mock_uc.execute.side_effect = ConflictException("Transición no permitida")
    app.dependency_overrides[_get_send_uc] = lambda: mock_uc

    with patch(_DECODE_PATH, return_value=_MANAGER_CLAIMS):
        async with client as c:
            response = await c.post("/api/v1/estimates/est-001/send", headers=_AUTH_HEADERS)

    assert response.status_code == 409


# ---------------------------------------------------------------------------
# POST /api/v1/estimates/{id}/convert
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_convert_estimate_success(client: AsyncClient) -> None:
    mock_uc = AsyncMock(spec=ConvertEstimateUseCase)
    mock_uc.execute.return_value = None
    app.dependency_overrides[_get_convert_uc] = lambda: mock_uc

    with patch(_DECODE_PATH, return_value=_MANAGER_CLAIMS):
        async with client as c:
            response = await c.post("/api/v1/estimates/est-001/convert", headers=_AUTH_HEADERS)

    assert response.status_code == 204


@pytest.mark.asyncio
async def test_convert_estimate_not_accepted_rejected(client: AsyncClient) -> None:
    mock_uc = AsyncMock(spec=ConvertEstimateUseCase)
    mock_uc.execute.side_effect = ConflictException("Transición no permitida")
    app.dependency_overrides[_get_convert_uc] = lambda: mock_uc

    with patch(_DECODE_PATH, return_value=_MANAGER_CLAIMS):
        async with client as c:
            response = await c.post("/api/v1/estimates/est-001/convert", headers=_AUTH_HEADERS)

    assert response.status_code == 409


# ---------------------------------------------------------------------------
# GET /api/v1/estimates/public/{token} — portal público
# ---------------------------------------------------------------------------


def _mock_estimate_repo(estimate: Estimate | None) -> EstimateRepository:
    repo = MagicMock(spec=EstimateRepository)
    repo.find_by_id.return_value = estimate
    repo.update.return_value = None
    return repo


def _mock_item_repo(items: list[EstimateItem]) -> EstimateItemRepository:
    repo = MagicMock(spec=EstimateItemRepository)
    repo.list_by_estimate.return_value = items
    return repo


def _mock_token_repo(token: PublicToken | None) -> PublicTokenRepository:
    repo = MagicMock(spec=PublicTokenRepository)
    repo.find_by_id.return_value = token
    return repo


def _valid_budget_token(estimate_id: str = "est-001") -> str:
    now = int(time.time())
    return encode_token(
        resource_id=estimate_id,
        tenant_id="tenant-abc",
        token_id="tok-001",
        iat=now,
        exp=now + 86400,
        secret=_SECRET,
    )


@pytest.mark.asyncio
async def test_public_view_estimate_success(client: AsyncClient) -> None:
    token = _valid_budget_token()
    estimate = _make_estimate(status=STATUS_SENT)
    app.dependency_overrides[_get_estimate_repo] = lambda: _mock_estimate_repo(estimate)
    app.dependency_overrides[_get_item_repo] = lambda: _mock_item_repo([_make_item()])
    app.dependency_overrides[_get_token_repo] = lambda: _mock_token_repo(_make_public_token())

    with patch("app.core.config.settings.HMAC_SECRET_KEY", _SECRET):
        async with client as c:
            response = await c.get(f"/api/v1/estimates/public/{token}")

    assert response.status_code == 200
    data = response.json()
    assert data["number"] == "EST-2024-000001"
    assert len(data["items"]) == 1


@pytest.mark.asyncio
async def test_public_view_invalid_token(client: AsyncClient) -> None:
    async with client as c:
        response = await c.get("/api/v1/estimates/public/not-a-valid-token")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_public_view_revoked_token(client: AsyncClient) -> None:
    token = _valid_budget_token()
    app.dependency_overrides[_get_estimate_repo] = lambda: _mock_estimate_repo(_make_estimate())
    app.dependency_overrides[_get_item_repo] = lambda: _mock_item_repo([])
    app.dependency_overrides[_get_token_repo] = lambda: _mock_token_repo(
        _make_public_token(revoked=True)
    )

    with patch("app.core.config.settings.HMAC_SECRET_KEY", _SECRET):
        async with client as c:
            response = await c.get(f"/api/v1/estimates/public/{token}")

    assert response.status_code == 409


# ---------------------------------------------------------------------------
# POST /api/v1/estimates/public/{token}/respond
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_public_respond_accept_success(client: AsyncClient) -> None:
    token = _valid_budget_token()
    estimate = _make_estimate(status=STATUS_VIEWED)
    app.dependency_overrides[_get_estimate_repo] = lambda: _mock_estimate_repo(estimate)
    app.dependency_overrides[_get_token_repo] = lambda: _mock_token_repo(_make_public_token())

    with patch("app.core.config.settings.HMAC_SECRET_KEY", _SECRET):
        async with client as c:
            response = await c.post(
                f"/api/v1/estimates/public/{token}/respond",
                json={"accepted": True, "client_notes": "Muy bien"},
            )

    assert response.status_code == 204


@pytest.mark.asyncio
async def test_public_respond_reject_success(client: AsyncClient) -> None:
    token = _valid_budget_token()
    estimate = _make_estimate(status=STATUS_VIEWED)
    app.dependency_overrides[_get_estimate_repo] = lambda: _mock_estimate_repo(estimate)
    app.dependency_overrides[_get_token_repo] = lambda: _mock_token_repo(_make_public_token())

    with patch("app.core.config.settings.HMAC_SECRET_KEY", _SECRET):
        async with client as c:
            response = await c.post(
                f"/api/v1/estimates/public/{token}/respond",
                json={"accepted": False, "client_notes": "Precio muy alto"},
            )

    assert response.status_code == 204


@pytest.mark.asyncio
async def test_public_respond_invalid_token(client: AsyncClient) -> None:
    async with client as c:
        response = await c.post(
            "/api/v1/estimates/public/garbage/respond", json={"accepted": True}
        )
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# Use case unit tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_send_use_case_creates_public_token() -> None:
    estimate = _make_estimate(status=STATUS_DRAFT)
    mock_estimate_repo = MagicMock(spec=EstimateRepository)
    mock_estimate_repo.find_by_id.return_value = estimate
    mock_estimate_repo.update.return_value = None

    mock_token_repo = MagicMock(spec=PublicTokenRepository)
    mock_token_repo.create.return_value = None

    uc = SendEstimateUseCase(mock_estimate_repo, mock_token_repo)

    with patch("app.features.estimates.application.workflow_use_cases.settings") as mock_settings:
        mock_settings.HMAC_SECRET_KEY = _SECRET
        mock_settings.PUBLIC_BASE_URL = "https://example.com"
        url = await uc.execute("tenant-abc", "est-001", "uid-manager")

    assert "example.com" in url
    mock_token_repo.create.assert_called_once()
    mock_estimate_repo.update.assert_called_once()


@pytest.mark.asyncio
async def test_send_use_case_wrong_status() -> None:
    estimate = _make_estimate(status=STATUS_SENT)
    mock_repo = MagicMock(spec=EstimateRepository)
    mock_repo.find_by_id.return_value = estimate

    uc = SendEstimateUseCase(mock_repo, MagicMock(spec=PublicTokenRepository))
    with pytest.raises(ConflictException):
        await uc.execute("tenant-abc", "est-001", "uid")


@pytest.mark.asyncio
async def test_delete_use_case_rejects_sent_estimate() -> None:
    from app.features.estimates.application.use_cases import DeleteEstimateUseCase

    estimate = _make_estimate(status=STATUS_SENT)
    mock_repo = MagicMock(spec=EstimateRepository)
    mock_repo.find_by_id.return_value = estimate

    uc = DeleteEstimateUseCase(mock_repo)
    with pytest.raises(ConflictException):
        await uc.execute("tenant-abc", "est-001", "uid")
