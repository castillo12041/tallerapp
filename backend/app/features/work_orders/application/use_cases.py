from __future__ import annotations

import uuid
from datetime import datetime, timezone

from app.core.exceptions import ConflictException, NotFoundException
from app.core.utils import run_sync
from app.features.estimates.infrastructure.estimate_repository import EstimateRepository
from app.features.inspections.infrastructure.inspection_repository import InspectionRepository
from app.features.users.infrastructure.user_crud_repository import UserCrudRepository
from app.features.work_orders.domain.entities import WorkOrder, WorkOrderEntry
from app.features.work_orders.domain.workflow import STATUS_PENDING
from app.features.work_orders.infrastructure.counter_repository import (
    WorkOrderCounterRepository,
)
from app.features.work_orders.infrastructure.entry_repository import WorkOrderEntryRepository
from app.features.work_orders.infrastructure.work_order_repository import WorkOrderRepository


class CreateWorkOrderUseCase:
    def __init__(
        self,
        work_order_repo: WorkOrderRepository,
        entry_repo: WorkOrderEntryRepository,
        counter_repo: WorkOrderCounterRepository,
        estimate_repo: EstimateRepository,
        inspection_repo: InspectionRepository,
        user_repo: UserCrudRepository,
    ) -> None:
        self._work_orders = work_order_repo
        self._entries = entry_repo
        self._counter = counter_repo
        self._estimates = estimate_repo
        self._inspections = inspection_repo
        self._users = user_repo

    async def execute(
        self,
        tenant_id: str,
        mechanic_id: str,
        created_by: str,
        estimate_id: str | None = None,
        inspection_id: str | None = None,
        notes: str | None = None,
        diagnosis: str | None = None,
    ) -> WorkOrder:
        if not estimate_id and not inspection_id:
            raise ConflictException(
                "Se debe vincular a un presupuesto o una inspección"
            )

        mechanic = await run_sync(self._users.find_by_uid_in_tenant, mechanic_id, tenant_id)
        if mechanic is None:
            raise NotFoundException(f"Mecánico '{mechanic_id}' no encontrado")

        vehicle_snapshot = None
        client_snapshot = None

        if estimate_id:
            estimate = await run_sync(self._estimates.find_by_id, estimate_id, tenant_id)
            if estimate is None:
                raise NotFoundException(f"Presupuesto '{estimate_id}' no encontrado")
            vehicle_snapshot = estimate.vehicle_snapshot
            client_snapshot = estimate.client_snapshot
            if not inspection_id:
                inspection_id = estimate.inspection_id

        if inspection_id and vehicle_snapshot is None:
            inspection = await run_sync(
                self._inspections.find_by_id, inspection_id, tenant_id
            )
            if inspection is None:
                raise NotFoundException(f"Inspección '{inspection_id}' no encontrada")
            vehicle_snapshot = inspection.vehicle_snapshot
            client_snapshot = inspection.client_snapshot

        if vehicle_snapshot is None:
            raise ConflictException("No se pudo obtener snapshot del vehículo")

        now = datetime.now(timezone.utc)
        work_order_id = str(uuid.uuid4())
        number = await run_sync(self._counter.next_number, tenant_id, now.year)

        mechanic_name = mechanic.display_name

        vs = vehicle_snapshot
        cs = client_snapshot

        doc: dict = {
            "id": work_order_id,
            "tenantId": tenant_id,
            "number": number,
            "status": STATUS_PENDING,
            "estimateId": estimate_id,
            "inspectionId": inspection_id,
            "vehicleSnapshot": {
                "id": vs.id, "plate": vs.plate, "make": vs.make, "model": vs.model,
                "year": getattr(vs, "year", None), "color": getattr(vs, "color", None),
                "vin": getattr(vs, "vin", None),
            },
            "clientSnapshot": {
                "id": cs.id, "fullName": cs.full_name, "email": cs.email,
                "phone": cs.phone, "rut": cs.rut,
            } if cs else None,
            "mechanicId": mechanic_id,
            "mechanicName": mechanic_name,
            "diagnosis": diagnosis,
            "notes": notes,
            "startedAt": None,
            "waitingPartsAt": None,
            "qualityCheckAt": None,
            "completedAt": None,
            "cancelledAt": None,
            "deletedAt": None,
            "createdAt": now,
            "updatedAt": now,
            "createdBy": created_by,
            "updatedBy": created_by,
        }

        await run_sync(self._work_orders.create, doc)
        return await run_sync(self._work_orders.find_by_id, work_order_id, tenant_id)  # type: ignore[return-value]


class GetWorkOrderUseCase:
    def __init__(
        self,
        work_order_repo: WorkOrderRepository,
        entry_repo: WorkOrderEntryRepository,
    ) -> None:
        self._work_orders = work_order_repo
        self._entries = entry_repo

    async def execute(
        self, tenant_id: str, work_order_id: str
    ) -> tuple[WorkOrder, list[WorkOrderEntry]]:
        wo = await run_sync(self._work_orders.find_by_id, work_order_id, tenant_id)
        if wo is None:
            raise NotFoundException(f"Orden de trabajo '{work_order_id}' no encontrada")
        entries = await run_sync(self._entries.list_by_work_order, work_order_id)
        return wo, entries


class ListWorkOrdersUseCase:
    def __init__(self, work_order_repo: WorkOrderRepository) -> None:
        self._work_orders = work_order_repo

    async def execute(
        self,
        tenant_id: str,
        status: str | None = None,
        mechanic_id: str | None = None,
        estimate_id: str | None = None,
    ) -> list[WorkOrder]:
        return await run_sync(
            self._work_orders.list_by_tenant, tenant_id, status, mechanic_id, estimate_id
        )


class UpdateWorkOrderUseCase:
    def __init__(self, work_order_repo: WorkOrderRepository) -> None:
        self._work_orders = work_order_repo

    async def execute(
        self,
        tenant_id: str,
        work_order_id: str,
        updated_by: str,
        fields: dict,
    ) -> WorkOrder:
        wo = await run_sync(self._work_orders.find_by_id, work_order_id, tenant_id)
        if wo is None:
            raise NotFoundException(f"Orden de trabajo '{work_order_id}' no encontrada")
        if wo.is_terminal:
            raise ConflictException(
                f"No se puede editar una OT en estado '{wo.status}'"
            )
        await run_sync(self._work_orders.update, work_order_id, tenant_id, fields, updated_by)
        return await run_sync(self._work_orders.find_by_id, work_order_id, tenant_id)  # type: ignore[return-value]
