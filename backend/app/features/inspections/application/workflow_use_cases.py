"""
Casos de uso de transiciones de estado de inspección.
"""

from __future__ import annotations

from datetime import datetime, timezone

from app.core.exceptions import NotFoundException
from app.core.utils import run_sync
from app.features.inspections.domain.entities import Inspection, InspectionItem
from app.features.inspections.domain.workflow import (
    STATUS_CANCELLED,
    STATUS_COMPLETED,
    STATUS_IN_PROGRESS,
    STATUS_REVIEW,
    compute_score,
    validate_transition,
)
from app.features.inspections.infrastructure.inspection_repository import (
    InspectionRepository,
)
from app.features.inspections.infrastructure.item_repository import ItemRepository


async def _get_or_raise(
    repo: InspectionRepository, inspection_id: str, tenant_id: str
) -> Inspection:
    inspection = await run_sync(repo.find_by_id, inspection_id, tenant_id)
    if inspection is None:
        raise NotFoundException(f"Inspección '{inspection_id}' no encontrada")
    return inspection


class StartInspectionUseCase:
    """draft → in_progress."""

    def __init__(self, repo: InspectionRepository) -> None:
        self._repo = repo

    async def execute(self, inspection_id: str, tenant_id: str, updated_by: str) -> Inspection:
        inspection = await _get_or_raise(self._repo, inspection_id, tenant_id)
        validate_transition(inspection.status, STATUS_IN_PROGRESS)
        await run_sync(
            self._repo.update,
            inspection_id, tenant_id,
            {"status": STATUS_IN_PROGRESS, "started_at": datetime.now(timezone.utc)},
            updated_by,
        )
        return await _get_or_raise(self._repo, inspection_id, tenant_id)


class UpdateItemUseCase:
    """Actualiza un ítem y recalcula los contadores del padre."""

    def __init__(self, inspection_repo: InspectionRepository, item_repo: ItemRepository) -> None:
        self._inspections = inspection_repo
        self._items = item_repo

    async def execute(
        self,
        inspection_id: str,
        item_id: str,
        tenant_id: str,
        fields: dict,
        updated_by: str,
    ) -> InspectionItem:
        inspection = await _get_or_raise(self._inspections, inspection_id, tenant_id)
        item = await run_sync(self._items.find_by_id, inspection_id, item_id)
        if item is None:
            raise NotFoundException(f"Ítem '{item_id}' no encontrado")

        await run_sync(self._items.update, inspection_id, item_id, fields, updated_by)

        # Recompute aggregates in parent
        counts = await run_sync(self._items.count_statuses, inspection_id)
        await run_sync(
            self._inspections.update,
            inspection_id, tenant_id,
            {
                "good_items": counts["good"],
                "regular_items": counts["regular"],
                "bad_items": counts["bad"],
                "na_items": counts["na"],
                "total_repair_cost": counts["total_repair_cost"],
            },
            updated_by,
        )
        updated_item = await run_sync(self._items.find_by_id, inspection_id, item_id)
        if updated_item is None:
            raise NotFoundException(f"Ítem '{item_id}' no encontrado")
        return updated_item


class SubmitInspectionUseCase:
    """in_progress → review."""

    def __init__(self, repo: InspectionRepository) -> None:
        self._repo = repo

    async def execute(self, inspection_id: str, tenant_id: str, updated_by: str) -> Inspection:
        inspection = await _get_or_raise(self._repo, inspection_id, tenant_id)
        validate_transition(inspection.status, STATUS_REVIEW)
        await run_sync(
            self._repo.update,
            inspection_id, tenant_id,
            {"status": STATUS_REVIEW},
            updated_by,
        )
        return await _get_or_raise(self._repo, inspection_id, tenant_id)


class CompleteInspectionUseCase:
    """review → completed. Calcula score automáticamente."""

    def __init__(self, repo: InspectionRepository) -> None:
        self._repo = repo

    async def execute(self, inspection_id: str, tenant_id: str, updated_by: str) -> Inspection:
        inspection = await _get_or_raise(self._repo, inspection_id, tenant_id)
        validate_transition(inspection.status, STATUS_COMPLETED)
        score = compute_score(
            inspection.good_items, inspection.regular_items,
            inspection.bad_items, inspection.na_items,
            inspection.total_items,
        )
        await run_sync(
            self._repo.update,
            inspection_id, tenant_id,
            {
                "status": STATUS_COMPLETED,
                "score": score,
                "completed_at": datetime.now(timezone.utc),
            },
            updated_by,
        )
        return await _get_or_raise(self._repo, inspection_id, tenant_id)


class ReopenInspectionUseCase:
    """review → in_progress."""

    def __init__(self, repo: InspectionRepository) -> None:
        self._repo = repo

    async def execute(self, inspection_id: str, tenant_id: str, updated_by: str) -> Inspection:
        inspection = await _get_or_raise(self._repo, inspection_id, tenant_id)
        validate_transition(inspection.status, STATUS_IN_PROGRESS)
        await run_sync(
            self._repo.update,
            inspection_id, tenant_id,
            {"status": STATUS_IN_PROGRESS},
            updated_by,
        )
        return await _get_or_raise(self._repo, inspection_id, tenant_id)


class CancelInspectionUseCase:
    def __init__(self, repo: InspectionRepository) -> None:
        self._repo = repo

    async def execute(self, inspection_id: str, tenant_id: str, updated_by: str) -> Inspection:
        inspection = await _get_or_raise(self._repo, inspection_id, tenant_id)
        validate_transition(inspection.status, STATUS_CANCELLED)
        await run_sync(
            self._repo.update,
            inspection_id, tenant_id,
            {"status": STATUS_CANCELLED},
            updated_by,
        )
        return await _get_or_raise(self._repo, inspection_id, tenant_id)
