from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.core.firebase import get_firestore
from app.dependencies.permissions import require_permission
from app.features.estimates.infrastructure.estimate_repository import EstimateRepository
from app.features.inspections.infrastructure.inspection_repository import InspectionRepository
from app.features.users.infrastructure.user_crud_repository import UserCrudRepository
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
from app.features.work_orders.infrastructure.counter_repository import (
    WorkOrderCounterRepository,
)
from app.features.work_orders.infrastructure.entry_repository import WorkOrderEntryRepository
from app.features.work_orders.infrastructure.work_order_repository import WorkOrderRepository
from app.features.work_orders.presentation.schemas import (
    AddEntryRequest,
    CancelWorkOrderRequest,
    ClientSnapshotOut,
    CreateWorkOrderRequest,
    UpdateWorkOrderRequest,
    VehicleSnapshotOut,
    WaitPartsRequest,
    WorkOrderEntryOut,
    WorkOrderListOut,
    WorkOrderOut,
    WorkOrderWithEntriesOut,
)
from app.schemas.auth import TokenPayload

router = APIRouter()


# ---------------------------------------------------------------------------
# Dependency factories
# ---------------------------------------------------------------------------


def _get_wo_repo() -> WorkOrderRepository:
    return WorkOrderRepository(db=get_firestore())


def _get_entry_repo() -> WorkOrderEntryRepository:
    return WorkOrderEntryRepository(db=get_firestore())


def _get_counter_repo() -> WorkOrderCounterRepository:
    return WorkOrderCounterRepository(db=get_firestore())


def _get_estimate_repo() -> EstimateRepository:
    return EstimateRepository(db=get_firestore())


def _get_inspection_repo() -> InspectionRepository:
    return InspectionRepository(db=get_firestore())


def _get_user_repo() -> UserCrudRepository:
    return UserCrudRepository(db=get_firestore())


def _get_create_uc(
    wo: Annotated[WorkOrderRepository, Depends(_get_wo_repo)],
    er: Annotated[WorkOrderEntryRepository, Depends(_get_entry_repo)],
    cr: Annotated[WorkOrderCounterRepository, Depends(_get_counter_repo)],
    est: Annotated[EstimateRepository, Depends(_get_estimate_repo)],
    ins: Annotated[InspectionRepository, Depends(_get_inspection_repo)],
    usr: Annotated[UserCrudRepository, Depends(_get_user_repo)],
) -> CreateWorkOrderUseCase:
    return CreateWorkOrderUseCase(wo, er, cr, est, ins, usr)


def _get_get_uc(
    wo: Annotated[WorkOrderRepository, Depends(_get_wo_repo)],
    er: Annotated[WorkOrderEntryRepository, Depends(_get_entry_repo)],
) -> GetWorkOrderUseCase:
    return GetWorkOrderUseCase(wo, er)


def _get_list_uc(
    wo: Annotated[WorkOrderRepository, Depends(_get_wo_repo)],
) -> ListWorkOrdersUseCase:
    return ListWorkOrdersUseCase(wo)


def _get_update_uc(
    wo: Annotated[WorkOrderRepository, Depends(_get_wo_repo)],
) -> UpdateWorkOrderUseCase:
    return UpdateWorkOrderUseCase(wo)


def _get_start_uc(
    wo: Annotated[WorkOrderRepository, Depends(_get_wo_repo)],
    er: Annotated[WorkOrderEntryRepository, Depends(_get_entry_repo)],
) -> StartWorkOrderUseCase:
    return StartWorkOrderUseCase(wo, er)


def _get_wait_parts_uc(
    wo: Annotated[WorkOrderRepository, Depends(_get_wo_repo)],
    er: Annotated[WorkOrderEntryRepository, Depends(_get_entry_repo)],
) -> WaitPartsUseCase:
    return WaitPartsUseCase(wo, er)


def _get_resume_uc(
    wo: Annotated[WorkOrderRepository, Depends(_get_wo_repo)],
    er: Annotated[WorkOrderEntryRepository, Depends(_get_entry_repo)],
) -> ResumeWorkOrderUseCase:
    return ResumeWorkOrderUseCase(wo, er)


def _get_quality_check_uc(
    wo: Annotated[WorkOrderRepository, Depends(_get_wo_repo)],
    er: Annotated[WorkOrderEntryRepository, Depends(_get_entry_repo)],
) -> QualityCheckUseCase:
    return QualityCheckUseCase(wo, er)


def _get_complete_uc(
    wo: Annotated[WorkOrderRepository, Depends(_get_wo_repo)],
    er: Annotated[WorkOrderEntryRepository, Depends(_get_entry_repo)],
) -> CompleteWorkOrderUseCase:
    return CompleteWorkOrderUseCase(wo, er)


def _get_cancel_uc(
    wo: Annotated[WorkOrderRepository, Depends(_get_wo_repo)],
    er: Annotated[WorkOrderEntryRepository, Depends(_get_entry_repo)],
) -> CancelWorkOrderUseCase:
    return CancelWorkOrderUseCase(wo, er)


def _get_add_entry_uc(
    wo: Annotated[WorkOrderRepository, Depends(_get_wo_repo)],
    er: Annotated[WorkOrderEntryRepository, Depends(_get_entry_repo)],
) -> AddEntryUseCase:
    return AddEntryUseCase(wo, er)


# ---------------------------------------------------------------------------
# Mapping helper
# ---------------------------------------------------------------------------


def _map_wo(wo, entries=None) -> dict:
    vs = wo.vehicle_snapshot
    cs = wo.client_snapshot
    base = {
        "id": wo.id, "number": wo.number, "status": wo.status,
        "tenant_id": wo.tenant_id, "estimate_id": wo.estimate_id,
        "inspection_id": wo.inspection_id,
        "vehicle_snapshot": VehicleSnapshotOut(
            id=vs.id, plate=vs.plate, make=vs.make, model=vs.model,
            year=vs.year, color=vs.color, vin=vs.vin,
        ),
        "client_snapshot": ClientSnapshotOut(
            id=cs.id, full_name=cs.full_name, email=cs.email,
            phone=cs.phone, rut=cs.rut,
        ) if cs else None,
        "mechanic_id": wo.mechanic_id, "mechanic_name": wo.mechanic_name,
        "diagnosis": wo.diagnosis, "notes": wo.notes,
        "started_at": wo.started_at, "waiting_parts_at": wo.waiting_parts_at,
        "quality_check_at": wo.quality_check_at, "completed_at": wo.completed_at,
        "cancelled_at": wo.cancelled_at,
        "created_at": wo.created_at, "updated_at": wo.updated_at,
        "created_by": wo.created_by,
    }
    if entries is not None:
        base["entries"] = [
            WorkOrderEntryOut(
                id=e.id, work_order_id=e.work_order_id, entry_type=e.entry_type,
                from_status=e.from_status, to_status=e.to_status, content=e.content,
                created_at=e.created_at, created_by=e.created_by,
            )
            for e in entries
        ]
    return base


# ---------------------------------------------------------------------------
# CRUD endpoints
# ---------------------------------------------------------------------------


@router.post(
    "",
    response_model=WorkOrderOut,
    status_code=201,
    summary="Crear orden de trabajo",
)
async def create_work_order(
    body: CreateWorkOrderRequest,
    current_user: Annotated[TokenPayload, Depends(require_permission("work_orders:create"))],
    uc: Annotated[CreateWorkOrderUseCase, Depends(_get_create_uc)],
) -> WorkOrderOut:
    wo = await uc.execute(
        tenant_id=current_user.tenant_id,  # type: ignore[arg-type]
        mechanic_id=body.mechanic_id,
        created_by=current_user.sub,
        estimate_id=body.estimate_id,
        inspection_id=body.inspection_id,
        notes=body.notes,
        diagnosis=body.diagnosis,
    )
    return WorkOrderOut(**_map_wo(wo))


@router.get(
    "",
    response_model=WorkOrderListOut,
    summary="Listar órdenes de trabajo",
)
async def list_work_orders(
    current_user: Annotated[TokenPayload, Depends(require_permission("work_orders:read"))],
    uc: Annotated[ListWorkOrdersUseCase, Depends(_get_list_uc)],
    status: str | None = Query(None),
    mechanic_id: str | None = Query(None),
    estimate_id: str | None = Query(None),
) -> WorkOrderListOut:
    work_orders = await uc.execute(
        tenant_id=current_user.tenant_id,  # type: ignore[arg-type]
        status=status,
        mechanic_id=mechanic_id,
        estimate_id=estimate_id,
    )
    items = [WorkOrderOut(**_map_wo(wo)) for wo in work_orders]
    return WorkOrderListOut(items=items, total=len(items))


@router.get(
    "/{work_order_id}",
    response_model=WorkOrderWithEntriesOut,
    summary="Obtener OT con bitácora",
)
async def get_work_order(
    work_order_id: str,
    current_user: Annotated[TokenPayload, Depends(require_permission("work_orders:read"))],
    uc: Annotated[GetWorkOrderUseCase, Depends(_get_get_uc)],
) -> WorkOrderWithEntriesOut:
    wo, entries = await uc.execute(
        tenant_id=current_user.tenant_id,  # type: ignore[arg-type]
        work_order_id=work_order_id,
    )
    return WorkOrderWithEntriesOut(**_map_wo(wo, entries))


@router.patch(
    "/{work_order_id}",
    response_model=WorkOrderOut,
    summary="Actualizar OT (campos generales, no workflow)",
)
async def update_work_order(
    work_order_id: str,
    body: UpdateWorkOrderRequest,
    current_user: Annotated[TokenPayload, Depends(require_permission("work_orders:update"))],
    uc: Annotated[UpdateWorkOrderUseCase, Depends(_get_update_uc)],
) -> WorkOrderOut:
    wo = await uc.execute(
        tenant_id=current_user.tenant_id,  # type: ignore[arg-type]
        work_order_id=work_order_id,
        updated_by=current_user.sub,
        fields=body.to_fields(),
    )
    return WorkOrderOut(**_map_wo(wo))


# ---------------------------------------------------------------------------
# Workflow endpoints
# ---------------------------------------------------------------------------


@router.post(
    "/{work_order_id}/start",
    status_code=204,
    summary="Iniciar OT (pending → in_progress)",
)
async def start_work_order(
    work_order_id: str,
    current_user: Annotated[TokenPayload, Depends(require_permission("work_orders:update"))],
    uc: Annotated[StartWorkOrderUseCase, Depends(_get_start_uc)],
) -> None:
    await uc.execute(
        tenant_id=current_user.tenant_id,  # type: ignore[arg-type]
        work_order_id=work_order_id,
        started_by=current_user.sub,
    )


@router.post(
    "/{work_order_id}/wait-parts",
    status_code=204,
    summary="Esperar repuestos (in_progress → waiting_parts)",
)
async def wait_parts(
    work_order_id: str,
    body: WaitPartsRequest,
    current_user: Annotated[TokenPayload, Depends(require_permission("work_orders:update"))],
    uc: Annotated[WaitPartsUseCase, Depends(_get_wait_parts_uc)],
) -> None:
    await uc.execute(
        tenant_id=current_user.tenant_id,  # type: ignore[arg-type]
        work_order_id=work_order_id,
        updated_by=current_user.sub,
        note=body.note,
    )


@router.post(
    "/{work_order_id}/resume",
    status_code=204,
    summary="Retomar trabajo (waiting_parts → in_progress)",
)
async def resume_work_order(
    work_order_id: str,
    current_user: Annotated[TokenPayload, Depends(require_permission("work_orders:update"))],
    uc: Annotated[ResumeWorkOrderUseCase, Depends(_get_resume_uc)],
) -> None:
    await uc.execute(
        tenant_id=current_user.tenant_id,  # type: ignore[arg-type]
        work_order_id=work_order_id,
        updated_by=current_user.sub,
    )


@router.post(
    "/{work_order_id}/quality-check",
    status_code=204,
    summary="Enviar a control de calidad (in_progress → quality_check)",
)
async def quality_check(
    work_order_id: str,
    current_user: Annotated[TokenPayload, Depends(require_permission("work_orders:update"))],
    uc: Annotated[QualityCheckUseCase, Depends(_get_quality_check_uc)],
) -> None:
    await uc.execute(
        tenant_id=current_user.tenant_id,  # type: ignore[arg-type]
        work_order_id=work_order_id,
        updated_by=current_user.sub,
    )


@router.post(
    "/{work_order_id}/complete",
    status_code=204,
    summary="Completar OT (quality_check → completed)",
)
async def complete_work_order(
    work_order_id: str,
    current_user: Annotated[TokenPayload, Depends(require_permission("work_orders:complete"))],
    uc: Annotated[CompleteWorkOrderUseCase, Depends(_get_complete_uc)],
) -> None:
    await uc.execute(
        tenant_id=current_user.tenant_id,  # type: ignore[arg-type]
        work_order_id=work_order_id,
        completed_by=current_user.sub,
    )


@router.post(
    "/{work_order_id}/cancel",
    status_code=204,
    summary="Cancelar OT",
)
async def cancel_work_order(
    work_order_id: str,
    body: CancelWorkOrderRequest,
    current_user: Annotated[TokenPayload, Depends(require_permission("work_orders:update"))],
    uc: Annotated[CancelWorkOrderUseCase, Depends(_get_cancel_uc)],
) -> None:
    await uc.execute(
        tenant_id=current_user.tenant_id,  # type: ignore[arg-type]
        work_order_id=work_order_id,
        cancelled_by=current_user.sub,
        reason=body.reason,
    )


@router.post(
    "/{work_order_id}/entries",
    status_code=201,
    summary="Agregar nota a la bitácora",
)
async def add_entry(
    work_order_id: str,
    body: AddEntryRequest,
    current_user: Annotated[TokenPayload, Depends(require_permission("work_orders:update"))],
    uc: Annotated[AddEntryUseCase, Depends(_get_add_entry_uc)],
) -> dict:
    await uc.execute(
        tenant_id=current_user.tenant_id,  # type: ignore[arg-type]
        work_order_id=work_order_id,
        content=body.content,
        created_by=current_user.sub,
    )
    return {"message": "Nota agregada correctamente"}
