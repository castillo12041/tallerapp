from __future__ import annotations

from datetime import datetime, timezone

from app.core.exceptions import NotFoundException
from app.core.utils import run_sync
from app.features.appointments.domain.entities import Appointment
from app.features.appointments.domain.workflow import (
    STATUS_CANCELLED,
    STATUS_CONFIRMED,
    validate_transition,
)
from app.features.appointments.infrastructure.appointment_repository import (
    AppointmentRepository,
)


class ConfirmAppointmentUseCase:
    def __init__(self, repo: AppointmentRepository) -> None:
        self._repo = repo

    async def execute(
        self, tenant_id: str, appointment_id: str, confirmed_by: str
    ) -> Appointment:
        appt = await run_sync(self._repo.find_by_id, appointment_id, tenant_id)
        if appt is None:
            raise NotFoundException(f"Cita '{appointment_id}' no encontrada")
        validate_transition(appt.status, STATUS_CONFIRMED)
        await run_sync(
            self._repo.update,
            appointment_id,
            tenant_id,
            {"status": STATUS_CONFIRMED},
            confirmed_by,
        )
        return await run_sync(self._repo.find_by_id, appointment_id, tenant_id)  # type: ignore[return-value]


class CancelAppointmentUseCase:
    def __init__(self, repo: AppointmentRepository) -> None:
        self._repo = repo

    async def execute(
        self,
        tenant_id: str,
        appointment_id: str,
        cancelled_by: str,
        reason: str | None = None,
    ) -> Appointment:
        appt = await run_sync(self._repo.find_by_id, appointment_id, tenant_id)
        if appt is None:
            raise NotFoundException(f"Cita '{appointment_id}' no encontrada")
        validate_transition(appt.status, STATUS_CANCELLED)
        now = datetime.now(timezone.utc)
        await run_sync(
            self._repo.update,
            appointment_id,
            tenant_id,
            {
                "status": STATUS_CANCELLED,
                "cancel_reason": reason,
                "cancelled_at": now,
            },
            cancelled_by,
        )
        return await run_sync(self._repo.find_by_id, appointment_id, tenant_id)  # type: ignore[return-value]
