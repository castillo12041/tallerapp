from __future__ import annotations

import uuid
from datetime import datetime, timezone

from app.core.exceptions import NotFoundException
from app.core.utils import run_sync
from app.features.work_orders.domain.workflow import (
    STATUS_CANCELLED,
    STATUS_COMPLETED,
    STATUS_IN_PROGRESS,
    STATUS_PENDING,
    STATUS_QUALITY_CHECK,
    STATUS_WAITING_PARTS,
    validate_transition,
)
from app.features.work_orders.infrastructure.entry_repository import WorkOrderEntryRepository
from app.features.work_orders.infrastructure.work_order_repository import WorkOrderRepository


def _status_entry(
    work_order_id: str,
    tenant_id: str,
    from_status: str,
    to_status: str,
    created_by: str,
) -> dict:
    now = datetime.now(timezone.utc)
    return {
        "id": str(uuid.uuid4()),
        "tenantId": tenant_id,
        "workOrderId": work_order_id,
        "entryType": "status_change",
        "fromStatus": from_status,
        "toStatus": to_status,
        "content": None,
        "createdAt": now,
        "createdBy": created_by,
    }


async def _transition(
    work_order_repo: WorkOrderRepository,
    entry_repo: WorkOrderEntryRepository,
    tenant_id: str,
    work_order_id: str,
    to_status: str,
    updated_by: str,
    extra_fields: dict | None = None,
) -> None:
    wo = await run_sync(work_order_repo.find_by_id, work_order_id, tenant_id)
    if wo is None:
        raise NotFoundException(f"Orden de trabajo '{work_order_id}' no encontrada")
    validate_transition(wo.status, to_status)

    fields = {"status": to_status, **(extra_fields or {})}
    await run_sync(work_order_repo.update, work_order_id, tenant_id, fields, updated_by)

    entry = _status_entry(work_order_id, tenant_id, wo.status, to_status, updated_by)
    await run_sync(entry_repo.add, work_order_id, entry)


class StartWorkOrderUseCase:
    """pending → in_progress"""

    def __init__(
        self, work_order_repo: WorkOrderRepository, entry_repo: WorkOrderEntryRepository
    ) -> None:
        self._work_orders = work_order_repo
        self._entries = entry_repo

    async def execute(self, tenant_id: str, work_order_id: str, started_by: str) -> None:
        now = datetime.now(timezone.utc)
        await _transition(
            self._work_orders, self._entries, tenant_id, work_order_id,
            STATUS_IN_PROGRESS, started_by, {"started_at": now},
        )


class WaitPartsUseCase:
    """in_progress → waiting_parts"""

    def __init__(
        self, work_order_repo: WorkOrderRepository, entry_repo: WorkOrderEntryRepository
    ) -> None:
        self._work_orders = work_order_repo
        self._entries = entry_repo

    async def execute(
        self,
        tenant_id: str,
        work_order_id: str,
        updated_by: str,
        note: str | None = None,
    ) -> None:
        wo = await run_sync(self._work_orders.find_by_id, work_order_id, tenant_id)
        if wo is None:
            raise NotFoundException(f"Orden de trabajo '{work_order_id}' no encontrada")
        validate_transition(wo.status, STATUS_WAITING_PARTS)

        now = datetime.now(timezone.utc)
        await run_sync(
            self._work_orders.update, work_order_id, tenant_id,
            {"status": STATUS_WAITING_PARTS, "waiting_parts_at": now}, updated_by,
        )
        entry: dict = {
            "id": str(uuid.uuid4()),
            "tenantId": tenant_id,
            "workOrderId": work_order_id,
            "entryType": "status_change",
            "fromStatus": wo.status,
            "toStatus": STATUS_WAITING_PARTS,
            "content": note,
            "createdAt": now,
            "createdBy": updated_by,
        }
        await run_sync(self._entries.add, work_order_id, entry)


class ResumeWorkOrderUseCase:
    """waiting_parts → in_progress"""

    def __init__(
        self, work_order_repo: WorkOrderRepository, entry_repo: WorkOrderEntryRepository
    ) -> None:
        self._work_orders = work_order_repo
        self._entries = entry_repo

    async def execute(self, tenant_id: str, work_order_id: str, updated_by: str) -> None:
        await _transition(
            self._work_orders, self._entries, tenant_id, work_order_id,
            STATUS_IN_PROGRESS, updated_by,
        )


class QualityCheckUseCase:
    """in_progress → quality_check"""

    def __init__(
        self, work_order_repo: WorkOrderRepository, entry_repo: WorkOrderEntryRepository
    ) -> None:
        self._work_orders = work_order_repo
        self._entries = entry_repo

    async def execute(self, tenant_id: str, work_order_id: str, updated_by: str) -> None:
        now = datetime.now(timezone.utc)
        await _transition(
            self._work_orders, self._entries, tenant_id, work_order_id,
            STATUS_QUALITY_CHECK, updated_by, {"quality_check_at": now},
        )


class CompleteWorkOrderUseCase:
    """quality_check → completed"""

    def __init__(
        self, work_order_repo: WorkOrderRepository, entry_repo: WorkOrderEntryRepository
    ) -> None:
        self._work_orders = work_order_repo
        self._entries = entry_repo

    async def execute(self, tenant_id: str, work_order_id: str, completed_by: str) -> None:
        now = datetime.now(timezone.utc)
        await _transition(
            self._work_orders, self._entries, tenant_id, work_order_id,
            STATUS_COMPLETED, completed_by, {"completed_at": now},
        )


class CancelWorkOrderUseCase:
    """any non-terminal → cancelled"""

    def __init__(
        self, work_order_repo: WorkOrderRepository, entry_repo: WorkOrderEntryRepository
    ) -> None:
        self._work_orders = work_order_repo
        self._entries = entry_repo

    async def execute(
        self,
        tenant_id: str,
        work_order_id: str,
        cancelled_by: str,
        reason: str | None = None,
    ) -> None:
        now = datetime.now(timezone.utc)
        wo = await run_sync(self._work_orders.find_by_id, work_order_id, tenant_id)
        if wo is None:
            raise NotFoundException(f"Orden de trabajo '{work_order_id}' no encontrada")
        validate_transition(wo.status, STATUS_CANCELLED)

        await run_sync(
            self._work_orders.update, work_order_id, tenant_id,
            {"status": STATUS_CANCELLED, "cancelled_at": now}, cancelled_by,
        )
        entry: dict = {
            "id": str(uuid.uuid4()),
            "tenantId": tenant_id,
            "workOrderId": work_order_id,
            "entryType": "status_change",
            "fromStatus": wo.status,
            "toStatus": STATUS_CANCELLED,
            "content": reason,
            "createdAt": now,
            "createdBy": cancelled_by,
        }
        await run_sync(self._entries.add, work_order_id, entry)


class AddEntryUseCase:
    """Agrega una nota libre a la bitácora de la OT."""

    def __init__(
        self, work_order_repo: WorkOrderRepository, entry_repo: WorkOrderEntryRepository
    ) -> None:
        self._work_orders = work_order_repo
        self._entries = entry_repo

    async def execute(
        self,
        tenant_id: str,
        work_order_id: str,
        content: str,
        created_by: str,
    ) -> None:
        wo = await run_sync(self._work_orders.find_by_id, work_order_id, tenant_id)
        if wo is None:
            raise NotFoundException(f"Orden de trabajo '{work_order_id}' no encontrada")
        now = datetime.now(timezone.utc)
        entry: dict = {
            "id": str(uuid.uuid4()),
            "tenantId": tenant_id,
            "workOrderId": work_order_id,
            "entryType": "note",
            "fromStatus": None,
            "toStatus": None,
            "content": content,
            "createdAt": now,
            "createdBy": created_by,
        }
        await run_sync(self._entries.add, work_order_id, entry)
