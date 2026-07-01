from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.core.exceptions import ForbiddenException
from app.core.firebase import get_firestore
from app.dependencies.permissions import require_permission
from app.features.clients.infrastructure.client_repository import ClientRepository
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
from app.features.inspections.infrastructure.counter_repository import (
    InspectionCounterRepository,
)
from app.features.inspections.infrastructure.inspection_repository import (
    InspectionRepository,
)
from app.features.inspections.infrastructure.item_repository import ItemRepository
from app.features.inspections.presentation.schemas import (
    CreateInspectionRequest,
    InspectionItemResponse,
    InspectionResponse,
    UpdateInspectionRequest,
    UpdateItemRequest,
)
from app.features.templates.infrastructure.template_repository import TemplateRepository
from app.features.vehicles.infrastructure.vehicle_repository import VehicleRepository
from app.schemas.auth import TokenPayload

router = APIRouter()


# ---------------------------------------------------------------------------
# Dependency factories
# ---------------------------------------------------------------------------


def _get_inspection_repo() -> InspectionRepository:
    return InspectionRepository(db=get_firestore())


def _get_item_repo() -> ItemRepository:
    return ItemRepository(db=get_firestore())


def _get_create_uc(
    ir: Annotated[InspectionRepository, Depends(_get_inspection_repo)],
    item_r: Annotated[ItemRepository, Depends(_get_item_repo)],
) -> CreateInspectionUseCase:
    db = get_firestore()
    return CreateInspectionUseCase(
        inspection_repo=ir,
        item_repo=item_r,
        template_repo=TemplateRepository(db=db),
        vehicle_repo=VehicleRepository(db=db),
        client_repo=ClientRepository(db=db),
        counter_repo=InspectionCounterRepository(db=db),
    )


def _get_get_uc(
    ir: Annotated[InspectionRepository, Depends(_get_inspection_repo)],
    item_r: Annotated[ItemRepository, Depends(_get_item_repo)],
) -> GetInspectionUseCase:
    return GetInspectionUseCase(repo=ir, item_repo=item_r)


def _get_list_uc(ir: Annotated[InspectionRepository, Depends(_get_inspection_repo)]) -> ListInspectionsUseCase:
    return ListInspectionsUseCase(ir)


def _get_start_uc(ir: Annotated[InspectionRepository, Depends(_get_inspection_repo)]) -> StartInspectionUseCase:
    return StartInspectionUseCase(ir)


def _get_update_item_uc(
    ir: Annotated[InspectionRepository, Depends(_get_inspection_repo)],
    item_r: Annotated[ItemRepository, Depends(_get_item_repo)],
) -> UpdateItemUseCase:
    return UpdateItemUseCase(ir, item_r)


def _get_submit_uc(ir: Annotated[InspectionRepository, Depends(_get_inspection_repo)]) -> SubmitInspectionUseCase:
    return SubmitInspectionUseCase(ir)


def _get_complete_uc(ir: Annotated[InspectionRepository, Depends(_get_inspection_repo)]) -> CompleteInspectionUseCase:
    return CompleteInspectionUseCase(ir)


def _get_reopen_uc(ir: Annotated[InspectionRepository, Depends(_get_inspection_repo)]) -> ReopenInspectionUseCase:
    return ReopenInspectionUseCase(ir)


def _get_cancel_uc(ir: Annotated[InspectionRepository, Depends(_get_inspection_repo)]) -> CancelInspectionUseCase:
    return CancelInspectionUseCase(ir)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("/", response_model=InspectionResponse, status_code=201, summary="Crear inspección")
async def create_inspection(
    body: CreateInspectionRequest,
    current_user: Annotated[TokenPayload, Depends(require_permission("inspections:create"))],
    use_case: Annotated[CreateInspectionUseCase, Depends(_get_create_uc)],
) -> InspectionResponse:
    inspection = await use_case.execute(
        tenant_id=_tenant(current_user),
        vehicle_id=body.vehicle_id,
        mechanic_id=body.mechanic_id,
        created_by=current_user.sub,
        client_id=body.client_id,
        template_id=body.template_id,
        mileage_at_inspection=body.mileage_at_inspection,
        fuel_level=body.fuel_level,
    )
    return InspectionResponse.from_entity(inspection)


@router.get("/", response_model=list[InspectionResponse], summary="Listar inspecciones")
async def list_inspections(
    current_user: Annotated[TokenPayload, Depends(require_permission("inspections:read"))],
    use_case: Annotated[ListInspectionsUseCase, Depends(_get_list_uc)],
    status: str | None = Query(None),
    vehicle_id: str | None = Query(None),
    mechanic_id: str | None = Query(None),
) -> list[InspectionResponse]:
    inspections = await use_case.execute(
        _tenant(current_user), status=status, vehicle_id=vehicle_id, mechanic_id=mechanic_id
    )
    return [InspectionResponse.from_entity(i) for i in inspections]


@router.get("/{inspection_id}", response_model=InspectionResponse, summary="Obtener inspección")
async def get_inspection(
    inspection_id: str,
    current_user: Annotated[TokenPayload, Depends(require_permission("inspections:read"))],
    use_case: Annotated[GetInspectionUseCase, Depends(_get_get_uc)],
) -> InspectionResponse:
    inspection, items = await use_case.execute(inspection_id, _tenant(current_user))
    return InspectionResponse.from_entity(inspection, items)


@router.patch("/{inspection_id}", response_model=InspectionResponse, summary="Actualizar campos generales")
async def update_inspection(
    inspection_id: str,
    body: UpdateInspectionRequest,
    current_user: Annotated[TokenPayload, Depends(require_permission("inspections:update"))],
    ir: Annotated[InspectionRepository, Depends(_get_inspection_repo)],
) -> InspectionResponse:
    from app.core.exceptions import NotFoundException
    from app.core.utils import run_sync
    await run_sync(ir.update, inspection_id, _tenant(current_user), body.model_dump(exclude_none=True), current_user.sub)
    inspection = await run_sync(ir.find_by_id, inspection_id, _tenant(current_user))
    if inspection is None:
        raise NotFoundException(f"Inspección '{inspection_id}' no encontrada")
    return InspectionResponse.from_entity(inspection)


@router.post("/{inspection_id}/start", response_model=InspectionResponse, summary="Iniciar inspección (draft→in_progress)")
async def start_inspection(
    inspection_id: str,
    current_user: Annotated[TokenPayload, Depends(require_permission("inspections:update"))],
    use_case: Annotated[StartInspectionUseCase, Depends(_get_start_uc)],
) -> InspectionResponse:
    inspection = await use_case.execute(inspection_id, _tenant(current_user), current_user.sub)
    return InspectionResponse.from_entity(inspection)


@router.patch("/{inspection_id}/items/{item_id}", response_model=InspectionItemResponse, summary="Actualizar ítem")
async def update_item(
    inspection_id: str,
    item_id: str,
    body: UpdateItemRequest,
    current_user: Annotated[TokenPayload, Depends(require_permission("inspections:update"))],
    use_case: Annotated[UpdateItemUseCase, Depends(_get_update_item_uc)],
) -> InspectionItemResponse:
    item = await use_case.execute(
        inspection_id=inspection_id, item_id=item_id,
        tenant_id=_tenant(current_user),
        fields=body.model_dump(exclude_none=True),
        updated_by=current_user.sub,
    )
    return InspectionItemResponse.from_entity(item)


@router.post("/{inspection_id}/submit", response_model=InspectionResponse, summary="Enviar a revisión (in_progress→review)")
async def submit_inspection(
    inspection_id: str,
    current_user: Annotated[TokenPayload, Depends(require_permission("inspections:update"))],
    use_case: Annotated[SubmitInspectionUseCase, Depends(_get_submit_uc)],
) -> InspectionResponse:
    inspection = await use_case.execute(inspection_id, _tenant(current_user), current_user.sub)
    return InspectionResponse.from_entity(inspection)


@router.post("/{inspection_id}/complete", response_model=InspectionResponse, summary="Completar y calcular score (review→completed)")
async def complete_inspection(
    inspection_id: str,
    current_user: Annotated[TokenPayload, Depends(require_permission("inspections:complete"))],
    use_case: Annotated[CompleteInspectionUseCase, Depends(_get_complete_uc)],
) -> InspectionResponse:
    inspection = await use_case.execute(inspection_id, _tenant(current_user), current_user.sub)
    return InspectionResponse.from_entity(inspection)


@router.post("/{inspection_id}/reopen", response_model=InspectionResponse, summary="Reabrir inspección (review→in_progress)")
async def reopen_inspection(
    inspection_id: str,
    current_user: Annotated[TokenPayload, Depends(require_permission("inspections:review"))],
    use_case: Annotated[ReopenInspectionUseCase, Depends(_get_reopen_uc)],
) -> InspectionResponse:
    inspection = await use_case.execute(inspection_id, _tenant(current_user), current_user.sub)
    return InspectionResponse.from_entity(inspection)


@router.post("/{inspection_id}/cancel", response_model=InspectionResponse, summary="Cancelar inspección")
async def cancel_inspection(
    inspection_id: str,
    current_user: Annotated[TokenPayload, Depends(require_permission("inspections:review"))],
    use_case: Annotated[CancelInspectionUseCase, Depends(_get_cancel_uc)],
) -> InspectionResponse:
    inspection = await use_case.execute(inspection_id, _tenant(current_user), current_user.sub)
    return InspectionResponse.from_entity(inspection)


# ---------------------------------------------------------------------------


def _tenant(user: TokenPayload) -> str:
    if user.tenant_id:
        return user.tenant_id
    raise ForbiddenException("Se requiere contexto de taller")
