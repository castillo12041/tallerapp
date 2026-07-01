from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.core.firebase import get_firestore
from app.dependencies.permissions import require_permission
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
from app.features.appointments.infrastructure.appointment_repository import (
    AppointmentRepository,
)
from app.features.appointments.presentation.schemas import (
    AppointmentListOut,
    AppointmentOut,
    AvailabilityOut,
    AvailabilitySlotOut,
    CancelAppointmentRequest,
    CreateAppointmentRequest,
    UpdateAppointmentRequest,
)
from app.schemas.auth import TokenPayload

router = APIRouter()


# ---------------------------------------------------------------------------
# Dependency factories
# ---------------------------------------------------------------------------


def _get_repo() -> AppointmentRepository:
    return AppointmentRepository(db=get_firestore())


def _get_create_uc(repo: Annotated[AppointmentRepository, Depends(_get_repo)]) -> CreateAppointmentUseCase:
    return CreateAppointmentUseCase(repo)


def _get_get_uc(repo: Annotated[AppointmentRepository, Depends(_get_repo)]) -> GetAppointmentUseCase:
    return GetAppointmentUseCase(repo)


def _get_list_uc(repo: Annotated[AppointmentRepository, Depends(_get_repo)]) -> ListAppointmentsUseCase:
    return ListAppointmentsUseCase(repo)


def _get_update_uc(repo: Annotated[AppointmentRepository, Depends(_get_repo)]) -> UpdateAppointmentUseCase:
    return UpdateAppointmentUseCase(repo)


def _get_delete_uc(repo: Annotated[AppointmentRepository, Depends(_get_repo)]) -> DeleteAppointmentUseCase:
    return DeleteAppointmentUseCase(repo)


def _get_confirm_uc(repo: Annotated[AppointmentRepository, Depends(_get_repo)]) -> ConfirmAppointmentUseCase:
    return ConfirmAppointmentUseCase(repo)


def _get_cancel_uc(repo: Annotated[AppointmentRepository, Depends(_get_repo)]) -> CancelAppointmentUseCase:
    return CancelAppointmentUseCase(repo)


def _get_availability_uc(repo: Annotated[AppointmentRepository, Depends(_get_repo)]) -> GetAvailabilityUseCase:
    return GetAvailabilityUseCase(repo)


# ---------------------------------------------------------------------------
# Mapping helper
# ---------------------------------------------------------------------------


def _map(appt) -> dict:
    return {
        "id": appt.id,
        "tenant_id": appt.tenant_id,
        "type": appt.type,
        "status": appt.status,
        "title": appt.title,
        "start_at": appt.start_at,
        "end_at": appt.end_at,
        "all_day": appt.all_day,
        "client_id": appt.client_id,
        "vehicle_id": appt.vehicle_id,
        "mechanic_id": appt.mechanic_id,
        "mechanic_name": appt.mechanic_name,
        "inspection_id": appt.inspection_id,
        "work_order_id": appt.work_order_id,
        "notes": appt.notes,
        "reminder_minutes": appt.reminder_minutes,
        "cancel_reason": appt.cancel_reason,
        "cancelled_at": appt.cancelled_at,
        "created_at": appt.created_at,
        "updated_at": appt.updated_at,
        "created_by": appt.created_by,
    }


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get(
    "/availability",
    response_model=AvailabilityOut,
    summary="Slots disponibles por fecha y mecánico",
)
async def get_availability(
    current_user: Annotated[TokenPayload, Depends(require_permission("calendar:read"))],
    uc: Annotated[GetAvailabilityUseCase, Depends(_get_availability_uc)],
    date: str = Query(..., description="Fecha en formato YYYY-MM-DD"),
    mechanic_id: str | None = Query(None),
    duration_minutes: int = Query(60, ge=15, le=480),
) -> AvailabilityOut:
    parsed = datetime.strptime(date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    slots = await uc.execute(
        tenant_id=current_user.tenant_id,  # type: ignore[arg-type]
        date=parsed,
        mechanic_id=mechanic_id,
        duration_minutes=duration_minutes,
    )
    return AvailabilityOut(
        date=date,
        mechanic_id=mechanic_id,
        duration_minutes=duration_minutes,
        slots=[AvailabilitySlotOut(**s) for s in slots],
    )


@router.post(
    "",
    response_model=AppointmentOut,
    status_code=201,
    summary="Crear cita",
)
async def create_appointment(
    body: CreateAppointmentRequest,
    current_user: Annotated[TokenPayload, Depends(require_permission("calendar:create"))],
    uc: Annotated[CreateAppointmentUseCase, Depends(_get_create_uc)],
) -> AppointmentOut:
    appt = await uc.execute(
        tenant_id=current_user.tenant_id,  # type: ignore[arg-type]
        created_by=current_user.sub,
        appointment_type=body.type,
        title=body.title,
        start_at=body.start_at,
        end_at=body.end_at,
        all_day=body.all_day,
        client_id=body.client_id,
        vehicle_id=body.vehicle_id,
        mechanic_id=body.mechanic_id,
        mechanic_name=body.mechanic_name,
        inspection_id=body.inspection_id,
        work_order_id=body.work_order_id,
        notes=body.notes,
        reminder_minutes=body.reminder_minutes,
    )
    return AppointmentOut(**_map(appt))


@router.get(
    "",
    response_model=AppointmentListOut,
    summary="Listar citas",
)
async def list_appointments(
    current_user: Annotated[TokenPayload, Depends(require_permission("calendar:read"))],
    uc: Annotated[ListAppointmentsUseCase, Depends(_get_list_uc)],
    date: str | None = Query(None, description="Filtrar por fecha YYYY-MM-DD"),
    mechanic_id: str | None = Query(None),
    status: str | None = Query(None),
    type: str | None = Query(None),
) -> AppointmentListOut:
    date_start = None
    date_end = None
    if date:
        date_start = datetime.strptime(date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        date_end = date_start.replace(hour=23, minute=59, second=59)

    appointments = await uc.execute(
        tenant_id=current_user.tenant_id,  # type: ignore[arg-type]
        date_start=date_start,
        date_end=date_end,
        mechanic_id=mechanic_id,
        status=status,
        appointment_type=type,
    )
    items = [AppointmentOut(**_map(a)) for a in appointments]
    return AppointmentListOut(items=items, total=len(items))


@router.get(
    "/{appointment_id}",
    response_model=AppointmentOut,
    summary="Obtener cita",
)
async def get_appointment(
    appointment_id: str,
    current_user: Annotated[TokenPayload, Depends(require_permission("calendar:read"))],
    uc: Annotated[GetAppointmentUseCase, Depends(_get_get_uc)],
) -> AppointmentOut:
    appt = await uc.execute(
        tenant_id=current_user.tenant_id,  # type: ignore[arg-type]
        appointment_id=appointment_id,
    )
    return AppointmentOut(**_map(appt))


@router.patch(
    "/{appointment_id}",
    response_model=AppointmentOut,
    summary="Actualizar cita",
)
async def update_appointment(
    appointment_id: str,
    body: UpdateAppointmentRequest,
    current_user: Annotated[TokenPayload, Depends(require_permission("calendar:update"))],
    uc: Annotated[UpdateAppointmentUseCase, Depends(_get_update_uc)],
) -> AppointmentOut:
    appt = await uc.execute(
        tenant_id=current_user.tenant_id,  # type: ignore[arg-type]
        appointment_id=appointment_id,
        updated_by=current_user.sub,
        fields=body.to_fields(),
    )
    return AppointmentOut(**_map(appt))


@router.delete(
    "/{appointment_id}",
    status_code=204,
    summary="Eliminar cita (soft delete)",
)
async def delete_appointment(
    appointment_id: str,
    current_user: Annotated[TokenPayload, Depends(require_permission("calendar:delete"))],
    uc: Annotated[DeleteAppointmentUseCase, Depends(_get_delete_uc)],
) -> None:
    await uc.execute(
        tenant_id=current_user.tenant_id,  # type: ignore[arg-type]
        appointment_id=appointment_id,
        deleted_by=current_user.sub,
    )


@router.post(
    "/{appointment_id}/confirm",
    response_model=AppointmentOut,
    summary="Confirmar cita (scheduled → confirmed)",
)
async def confirm_appointment(
    appointment_id: str,
    current_user: Annotated[TokenPayload, Depends(require_permission("calendar:update"))],
    uc: Annotated[ConfirmAppointmentUseCase, Depends(_get_confirm_uc)],
) -> AppointmentOut:
    appt = await uc.execute(
        tenant_id=current_user.tenant_id,  # type: ignore[arg-type]
        appointment_id=appointment_id,
        confirmed_by=current_user.sub,
    )
    return AppointmentOut(**_map(appt))


@router.post(
    "/{appointment_id}/cancel",
    response_model=AppointmentOut,
    summary="Cancelar cita",
)
async def cancel_appointment(
    appointment_id: str,
    body: CancelAppointmentRequest,
    current_user: Annotated[TokenPayload, Depends(require_permission("calendar:update"))],
    uc: Annotated[CancelAppointmentUseCase, Depends(_get_cancel_uc)],
) -> AppointmentOut:
    appt = await uc.execute(
        tenant_id=current_user.tenant_id,  # type: ignore[arg-type]
        appointment_id=appointment_id,
        cancelled_by=current_user.sub,
        reason=body.reason,
    )
    return AppointmentOut(**_map(appt))
