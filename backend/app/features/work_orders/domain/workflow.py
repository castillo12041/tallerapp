from __future__ import annotations

from app.core.exceptions import ConflictException

STATUS_PENDING = "pending"
STATUS_IN_PROGRESS = "in_progress"
STATUS_WAITING_PARTS = "waiting_parts"
STATUS_QUALITY_CHECK = "quality_check"
STATUS_COMPLETED = "completed"
STATUS_CANCELLED = "cancelled"

ALL_STATUSES = {
    STATUS_PENDING,
    STATUS_IN_PROGRESS,
    STATUS_WAITING_PARTS,
    STATUS_QUALITY_CHECK,
    STATUS_COMPLETED,
    STATUS_CANCELLED,
}

_TRANSITIONS: dict[str, set[str]] = {
    STATUS_PENDING:       {STATUS_IN_PROGRESS, STATUS_CANCELLED},
    STATUS_IN_PROGRESS:   {STATUS_WAITING_PARTS, STATUS_QUALITY_CHECK, STATUS_CANCELLED},
    STATUS_WAITING_PARTS: {STATUS_IN_PROGRESS, STATUS_CANCELLED},
    STATUS_QUALITY_CHECK: {STATUS_COMPLETED, STATUS_IN_PROGRESS},
    STATUS_COMPLETED:     set(),
    STATUS_CANCELLED:     set(),
}


def validate_transition(from_status: str, to_status: str) -> None:
    allowed = _TRANSITIONS.get(from_status, set())
    if to_status not in allowed:
        raise ConflictException(
            f"Transición '{from_status}' → '{to_status}' no permitida. "
            f"Desde '{from_status}' se puede ir a: {sorted(allowed) or 'ninguno'}"
        )
