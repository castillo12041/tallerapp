from __future__ import annotations

from app.core.exceptions import ConflictException

STATUS_SCHEDULED = "scheduled"
STATUS_CONFIRMED = "confirmed"
STATUS_IN_PROGRESS = "in_progress"
STATUS_COMPLETED = "completed"
STATUS_CANCELLED = "cancelled"
STATUS_NO_SHOW = "no_show"

APPOINTMENT_TYPES = {"inspection", "work_order", "appointment", "reminder"}

_TRANSITIONS: dict[str, set[str]] = {
    STATUS_SCHEDULED:   {STATUS_CONFIRMED, STATUS_CANCELLED, STATUS_NO_SHOW},
    STATUS_CONFIRMED:   {STATUS_IN_PROGRESS, STATUS_CANCELLED, STATUS_NO_SHOW},
    STATUS_IN_PROGRESS: {STATUS_COMPLETED, STATUS_CANCELLED},
    STATUS_COMPLETED:   set(),
    STATUS_CANCELLED:   set(),
    STATUS_NO_SHOW:     set(),
}


def validate_transition(from_status: str, to_status: str) -> None:
    allowed = _TRANSITIONS.get(from_status, set())
    if to_status not in allowed:
        raise ConflictException(
            f"Transición '{from_status}' → '{to_status}' no permitida"
        )
