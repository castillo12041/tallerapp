"""
Estado de inspección y cálculo de puntuación.

Estados válidos: draft · in_progress · review · completed · cancelled
"""

from __future__ import annotations

from app.core.exceptions import ConflictException

STATUS_DRAFT = "draft"
STATUS_IN_PROGRESS = "in_progress"
STATUS_REVIEW = "review"
STATUS_COMPLETED = "completed"
STATUS_CANCELLED = "cancelled"

ALL_STATUSES = {STATUS_DRAFT, STATUS_IN_PROGRESS, STATUS_REVIEW, STATUS_COMPLETED, STATUS_CANCELLED}

# current_status → set of allowed next statuses
_VALID_TRANSITIONS: dict[str, set[str]] = {
    STATUS_DRAFT:       {STATUS_IN_PROGRESS, STATUS_CANCELLED},
    STATUS_IN_PROGRESS: {STATUS_REVIEW, STATUS_CANCELLED},
    STATUS_REVIEW:      {STATUS_COMPLETED, STATUS_IN_PROGRESS, STATUS_CANCELLED},
    STATUS_COMPLETED:   set(),
    STATUS_CANCELLED:   set(),
}

ITEM_STATUSES = {"pending", "good", "regular", "bad", "na"}


def validate_transition(current: str, next_status: str) -> None:
    """Lanza ConflictException si la transición no está permitida."""
    allowed = _VALID_TRANSITIONS.get(current, set())
    if next_status not in allowed:
        raise ConflictException(
            f"No se puede transicionar de '{current}' a '{next_status}'. "
            f"Transiciones permitidas: {sorted(allowed) or 'ninguna'}"
        )


def compute_score(good: int, regular: int, bad: int, na: int, total: int) -> float | None:
    """
    Calcula score 0–100. Solo evalúa ítems con resultado (no NA).
    Fórmula: (good*100 + regular*50) / (evaluated*100) * 100
    Retorna None si todos los ítems son NA o el total es 0.
    """
    evaluated = total - na
    if evaluated <= 0:
        return None
    score = (good * 100 + regular * 50) / (evaluated * 100) * 100
    return round(score, 1)
