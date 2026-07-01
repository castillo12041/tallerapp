from __future__ import annotations

from app.core.exceptions import ConflictException

STATUS_DRAFT = "draft"
STATUS_SENT = "sent"
STATUS_VIEWED = "viewed"
STATUS_ACCEPTED = "accepted"
STATUS_REJECTED = "rejected"
STATUS_CONVERTED = "converted"

ALL_STATUSES = {
    STATUS_DRAFT, STATUS_SENT, STATUS_VIEWED,
    STATUS_ACCEPTED, STATUS_REJECTED, STATUS_CONVERTED,
}

# Estados desde los que un cliente puede responder (aceptar o rechazar)
CLIENT_RESPONDABLE = {STATUS_SENT, STATUS_VIEWED}

_TRANSITIONS: dict[str, set[str]] = {
    STATUS_DRAFT:     {STATUS_SENT},
    STATUS_SENT:      {STATUS_VIEWED, STATUS_ACCEPTED, STATUS_REJECTED},
    STATUS_VIEWED:    {STATUS_ACCEPTED, STATUS_REJECTED},
    STATUS_ACCEPTED:  {STATUS_CONVERTED},
    STATUS_REJECTED:  set(),
    STATUS_CONVERTED: set(),
}


def validate_transition(from_status: str, to_status: str) -> None:
    allowed = _TRANSITIONS.get(from_status, set())
    if to_status not in allowed:
        raise ConflictException(
            f"Transición '{from_status}' → '{to_status}' no permitida. "
            f"Desde '{from_status}' se puede ir a: {sorted(allowed) or 'ninguno'}"
        )
