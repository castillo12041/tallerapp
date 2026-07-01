from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from app.core.exceptions import ConflictException, NotFoundException
from app.core.utils import run_sync
from app.features.appointments.domain.entities import Appointment
from app.features.appointments.domain.workflow import (
    STATUS_SCHEDULED,
    validate_transition,
)
from app.features.appointments.infrastructure.appointment_repository import (
    AppointmentRepository,
)

_SLOT_MINUTES = 60
_DAY_START_HOUR = 8
_DAY_END_HOUR = 18


class CreateAppointmentUseCase:
    def __init__(self, repo: AppointmentRepository) -> None:
        self._repo = repo

    async def execute(
        self,
        tenant_id: str,
        created_by: str,
        appointment_type: str,
        title: str,
        start_at: datetime,
        end_at: datetime,
        all_day: bool = False,
        client_id: str | None = None,
        vehicle_id: str | None = None,
        mechanic_id: str | None = None,
        mechanic_name: str | None = None,
        inspection_id: str | None = None,
        work_order_id: str | None = None,
        notes: str | None = None,
        reminder_minutes: int | None = None,
    ) -> Appointment:
        if end_at <= start_at:
            raise ConflictException("La fecha de fin debe ser posterior al inicio")

        if mechanic_id:
            conflicts = await run_sync(
                self._repo.find_conflicts, tenant_id, mechanic_id, start_at, end_at
            )
            if conflicts:
                raise ConflictException(
                    f"El mecánico tiene {len(conflicts)} cita(s) que se superponen en ese horario"
                )

        now = datetime.now(timezone.utc)
        appointment_id = str(uuid.uuid4())
        doc: dict = {
            "id": appointment_id,
            "tenantId": tenant_id,
            "type": appointment_type,
            "status": STATUS_SCHEDULED,
            "title": title,
            "startAt": start_at,
            "endAt": end_at,
            "allDay": all_day,
            "clientId": client_id,
            "vehicleId": vehicle_id,
            "mechanicId": mechanic_id,
            "mechanicName": mechanic_name,
            "inspectionId": inspection_id,
            "workOrderId": work_order_id,
            "notes": notes,
            "reminderMinutes": reminder_minutes,
            "cancelReason": None,
            "cancelledAt": None,
            "deletedAt": None,
            "createdAt": now,
            "updatedAt": now,
            "createdBy": created_by,
            "updatedBy": created_by,
        }
        await run_sync(self._repo.create, doc)
        return await run_sync(self._repo.find_by_id, appointment_id, tenant_id)  # type: ignore[return-value]


class GetAppointmentUseCase:
    def __init__(self, repo: AppointmentRepository) -> None:
        self._repo = repo

    async def execute(self, tenant_id: str, appointment_id: str) -> Appointment:
        appt = await run_sync(self._repo.find_by_id, appointment_id, tenant_id)
        if appt is None:
            raise NotFoundException(f"Cita '{appointment_id}' no encontrada")
        return appt


class ListAppointmentsUseCase:
    def __init__(self, repo: AppointmentRepository) -> None:
        self._repo = repo

    async def execute(
        self,
        tenant_id: str,
        date_start: datetime | None = None,
        date_end: datetime | None = None,
        mechanic_id: str | None = None,
        status: str | None = None,
        appointment_type: str | None = None,
    ) -> list[Appointment]:
        return await run_sync(
            self._repo.list_by_tenant,
            tenant_id,
            date_start,
            date_end,
            mechanic_id,
            status,
            appointment_type,
        )


class UpdateAppointmentUseCase:
    def __init__(self, repo: AppointmentRepository) -> None:
        self._repo = repo

    async def execute(
        self,
        tenant_id: str,
        appointment_id: str,
        updated_by: str,
        fields: dict,
    ) -> Appointment:
        appt = await run_sync(self._repo.find_by_id, appointment_id, tenant_id)
        if appt is None:
            raise NotFoundException(f"Cita '{appointment_id}' no encontrada")
        if appt.is_terminal:
            raise ConflictException(
                f"No se puede editar una cita en estado '{appt.status}'"
            )

        new_start = fields.get("start_at", appt.start_at)
        new_end = fields.get("end_at", appt.end_at)
        new_mechanic = fields.get("mechanic_id", appt.mechanic_id)

        if new_end <= new_start:
            raise ConflictException("La fecha de fin debe ser posterior al inicio")

        if new_mechanic:
            conflicts = await run_sync(
                self._repo.find_conflicts,
                tenant_id,
                new_mechanic,
                new_start,
                new_end,
                appointment_id,
            )
            if conflicts:
                raise ConflictException(
                    f"El mecánico tiene {len(conflicts)} cita(s) que se superponen en ese horario"
                )

        if "status" in fields:
            validate_transition(appt.status, fields["status"])

        await run_sync(self._repo.update, appointment_id, tenant_id, fields, updated_by)
        return await run_sync(self._repo.find_by_id, appointment_id, tenant_id)  # type: ignore[return-value]


class DeleteAppointmentUseCase:
    def __init__(self, repo: AppointmentRepository) -> None:
        self._repo = repo

    async def execute(self, tenant_id: str, appointment_id: str, deleted_by: str) -> None:
        appt = await run_sync(self._repo.find_by_id, appointment_id, tenant_id)
        if appt is None:
            raise NotFoundException(f"Cita '{appointment_id}' no encontrada")
        await run_sync(self._repo.soft_delete, appointment_id, deleted_by)


class GetAvailabilityUseCase:
    def __init__(self, repo: AppointmentRepository) -> None:
        self._repo = repo

    async def execute(
        self,
        tenant_id: str,
        date: datetime,
        mechanic_id: str | None = None,
        duration_minutes: int = _SLOT_MINUTES,
    ) -> list[dict]:
        day_start = date.replace(hour=_DAY_START_HOUR, minute=0, second=0, microsecond=0)
        day_end = date.replace(hour=_DAY_END_HOUR, minute=0, second=0, microsecond=0)

        booked = await run_sync(
            self._repo.list_by_tenant,
            tenant_id,
            day_start,
            day_end,
            mechanic_id,
            None,
            None,
        )
        active_booked = [a for a in booked if a.status not in {"cancelled", "no_show"}]

        slots: list[dict] = []
        current = day_start
        slot_delta = timedelta(minutes=duration_minutes)

        while current + slot_delta <= day_end:
            slot_end = current + slot_delta
            occupied = any(
                a.start_at < slot_end and a.end_at > current
                for a in active_booked
            )
            slots.append({
                "start_at": current,
                "end_at": slot_end,
                "available": not occupied,
            })
            current += slot_delta

        return slots
