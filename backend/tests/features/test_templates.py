"""
Tests del feature de plantillas de inspección.
"""

from __future__ import annotations

import time
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient

from app.core.exceptions import NotFoundException
from app.features.templates.application.use_cases import (
    CreateTemplateUseCase,
    DeleteTemplateUseCase,
    GetTemplateUseCase,
    ListTemplatesUseCase,
    UpdateTemplateUseCase,
)
from app.features.templates.domain.entities import (
    InspectionTemplate,
    TemplateCategory,
    TemplateItem,
)
from app.features.templates.presentation.router import (
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

_MANAGER_CLAIMS = {
    "sub": "uid-manager",
    "tenant_id": "tenant-abc",
    "role": "workshopmanager",
    "permissions": ["templates:manage", "inspections:read"],
    "plan": "professional",
    "type": "access",
    "exp": _NOW + 1800,
    "iat": _NOW,
}

_INSPECTOR_CLAIMS = {
    **_MANAGER_CLAIMS,
    "role": "inspector",
    "permissions": ["inspections:read"],
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_template(template_id: str = "tmpl-001") -> InspectionTemplate:
    now = datetime.now(timezone.utc)
    item = TemplateItem(id="item-01", name="Motor arranca", order=1)
    cat = TemplateCategory(id="cat-01", name="Motor", order=1, items=(item,))
    return InspectionTemplate(
        id=template_id,
        tenant_id="tenant-abc",
        name="Inspección Precompra Estándar",
        version=1,
        is_default=True,
        categories=(cat,),
        total_item_count=1,
        created_at=now,
        updated_at=now,
        created_by="uid-manager",
        updated_by="uid-manager",
    )


@pytest.fixture(autouse=True)
def clear_overrides():
    yield
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# POST /templates
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_template_success(client: AsyncClient) -> None:
    mock_uc = AsyncMock(spec=CreateTemplateUseCase)
    mock_uc.execute.return_value = _make_template()
    app.dependency_overrides[_get_create_uc] = lambda: mock_uc

    with patch(_DECODE_PATH, return_value=_MANAGER_CLAIMS):
        async with client as c:
            response = await c.post(
                "/api/v1/templates/",
                json={
                    "name": "Inspección Estándar",
                    "categories": [
                        {
                            "name": "Motor",
                            "order": 1,
                            "items": [{"name": "Motor arranca", "order": 1}],
                        }
                    ],
                },
                headers=_AUTH_HEADERS,
            )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Inspección Precompra Estándar"
    assert data["is_system"] is False
    mock_uc.execute.assert_called_once()


@pytest.mark.asyncio
async def test_create_template_missing_required(client: AsyncClient) -> None:
    with patch(_DECODE_PATH, return_value=_MANAGER_CLAIMS):
        async with client as c:
            response = await c.post(
                "/api/v1/templates/",
                json={"name": "Sin categorías", "categories": []},
                headers=_AUTH_HEADERS,
            )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_template_no_permission(client: AsyncClient) -> None:
    with patch(_DECODE_PATH, return_value=_INSPECTOR_CLAIMS):
        async with client as c:
            response = await c.post(
                "/api/v1/templates/",
                json={"name": "Plantilla", "categories": [{"name": "X", "order": 1, "items": []}]},
                headers=_AUTH_HEADERS,
            )

    assert response.status_code == 403


# ---------------------------------------------------------------------------
# GET /templates
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_templates_success(client: AsyncClient) -> None:
    mock_uc = AsyncMock(spec=ListTemplatesUseCase)
    mock_uc.execute.return_value = [_make_template("t1"), _make_template("t2")]
    app.dependency_overrides[_get_list_uc] = lambda: mock_uc

    with patch(_DECODE_PATH, return_value=_INSPECTOR_CLAIMS):
        async with client as c:
            response = await c.get("/api/v1/templates/", headers=_AUTH_HEADERS)

    assert response.status_code == 200
    assert len(response.json()) == 2


@pytest.mark.asyncio
async def test_list_templates_inspector_allowed(client: AsyncClient) -> None:
    mock_uc = AsyncMock(spec=ListTemplatesUseCase)
    mock_uc.execute.return_value = []
    app.dependency_overrides[_get_list_uc] = lambda: mock_uc

    with patch(_DECODE_PATH, return_value=_INSPECTOR_CLAIMS):
        async with client as c:
            response = await c.get("/api/v1/templates/", headers=_AUTH_HEADERS)

    assert response.status_code == 200


# ---------------------------------------------------------------------------
# GET /templates/{id}
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_template_success(client: AsyncClient) -> None:
    mock_uc = AsyncMock(spec=GetTemplateUseCase)
    mock_uc.execute.return_value = _make_template()
    app.dependency_overrides[_get_get_uc] = lambda: mock_uc

    with patch(_DECODE_PATH, return_value=_INSPECTOR_CLAIMS):
        async with client as c:
            response = await c.get("/api/v1/templates/tmpl-001", headers=_AUTH_HEADERS)

    assert response.status_code == 200
    assert response.json()["total_item_count"] == 1


@pytest.mark.asyncio
async def test_get_template_not_found(client: AsyncClient) -> None:
    mock_uc = AsyncMock(spec=GetTemplateUseCase)
    mock_uc.execute.side_effect = NotFoundException("Plantilla no encontrada")
    app.dependency_overrides[_get_get_uc] = lambda: mock_uc

    with patch(_DECODE_PATH, return_value=_INSPECTOR_CLAIMS):
        async with client as c:
            response = await c.get("/api/v1/templates/no-existe", headers=_AUTH_HEADERS)

    assert response.status_code == 404


# ---------------------------------------------------------------------------
# PATCH /templates/{id}
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_update_template_success(client: AsyncClient) -> None:
    mock_uc = AsyncMock(spec=UpdateTemplateUseCase)
    mock_uc.execute.return_value = _make_template()
    app.dependency_overrides[_get_update_uc] = lambda: mock_uc

    with patch(_DECODE_PATH, return_value=_MANAGER_CLAIMS):
        async with client as c:
            response = await c.patch(
                "/api/v1/templates/tmpl-001",
                json={"name": "Nuevo Nombre de Plantilla"},
                headers=_AUTH_HEADERS,
            )

    assert response.status_code == 200
    mock_uc.execute.assert_called_once()


# ---------------------------------------------------------------------------
# DELETE /templates/{id}
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_delete_template_success(client: AsyncClient) -> None:
    mock_uc = AsyncMock(spec=DeleteTemplateUseCase)
    mock_uc.execute.return_value = None
    app.dependency_overrides[_get_delete_uc] = lambda: mock_uc

    with patch(_DECODE_PATH, return_value=_MANAGER_CLAIMS):
        async with client as c:
            response = await c.delete("/api/v1/templates/tmpl-001", headers=_AUTH_HEADERS)

    assert response.status_code == 204


@pytest.mark.asyncio
async def test_delete_template_not_found(client: AsyncClient) -> None:
    mock_uc = AsyncMock(spec=DeleteTemplateUseCase)
    mock_uc.execute.side_effect = NotFoundException("Plantilla no encontrada")
    app.dependency_overrides[_get_delete_uc] = lambda: mock_uc

    with patch(_DECODE_PATH, return_value=_MANAGER_CLAIMS):
        async with client as c:
            response = await c.delete("/api/v1/templates/no-existe", headers=_AUTH_HEADERS)

    assert response.status_code == 404


# ---------------------------------------------------------------------------
# Domain entity tests
# ---------------------------------------------------------------------------


def test_template_is_deleted_when_deleted_at_set() -> None:
    now = datetime.now(timezone.utc)
    t = _make_template()
    t2 = InspectionTemplate(
        **{**t.__dict__, "deleted_at": now}  # type: ignore[arg-type]
    )
    assert t2.is_deleted


def test_template_system_when_tenant_id_none() -> None:
    now = datetime.now(timezone.utc)
    t = InspectionTemplate(
        id="sys-01", tenant_id=None, name="Sistema", version=1,
        is_default=True, categories=(), total_item_count=0,
        created_at=now, updated_at=now, created_by="system", updated_by="system",
    )
    assert t.is_system


def test_template_active_not_deleted() -> None:
    assert not _make_template().is_deleted
