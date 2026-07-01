"""
Casos de uso CRUD de inspecciones.
Los casos de uso de workflow están en workflow_use_cases.py.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from app.core.exceptions import NotFoundException
from app.core.utils import run_sync
from app.features.clients.infrastructure.client_repository import ClientRepository
from app.features.inspections.domain.entities import (
    ClientSnapshot,
    Inspection,
    InspectionItem,
    VehicleSnapshot,
)
from app.features.inspections.domain.workflow import STATUS_DRAFT
from app.features.inspections.infrastructure.counter_repository import (
    InspectionCounterRepository,
)
from app.features.inspections.infrastructure.inspection_repository import (
    InspectionRepository,
)
from app.features.inspections.infrastructure.item_repository import ItemRepository
from app.features.templates.infrastructure.template_repository import TemplateRepository
from app.features.vehicles.infrastructure.vehicle_repository import VehicleRepository


def _build_items_from_template(
    template_id: str,
    inspection_id: str,
    tenant_id: str,
    created_by: str,
    repo: TemplateRepository,
) -> list[dict]:
    template = repo.find_by_id(template_id)
    if template is None:
        return []
    now = datetime.now(timezone.utc)
    items: list[dict] = []
    for cat in template.categories:
        for it in cat.items:
            items.append({
                "id": str(uuid.uuid4()),
                "tenantId": tenant_id,
                "inspectionId": inspection_id,
                "category": cat.name,
                "categoryOrder": cat.order,
                "name": it.name,
                "order": it.order,
                "status": "pending",
                "observation": None,
                "repairCost": None,
                "photoUrls": [],
                "audioUrl": None,
                "photoCount": 0,
                "isOffline": False,
                "localPhotoIds": [],
                "createdAt": now,
                "updatedAt": now,
                "createdBy": created_by,
                "updatedBy": created_by,
                "deletedAt": None,
            })
    return items


class CreateInspectionUseCase:
    def __init__(
        self,
        inspection_repo: InspectionRepository,
        item_repo: ItemRepository,
        template_repo: TemplateRepository,
        vehicle_repo: VehicleRepository,
        client_repo: ClientRepository,
        counter_repo: InspectionCounterRepository,
    ) -> None:
        self._inspections = inspection_repo
        self._items = item_repo
        self._templates = template_repo
        self._vehicles = vehicle_repo
        self._clients = client_repo
        self._counter = counter_repo

    async def execute(
        self,
        tenant_id: str,
        vehicle_id: str,
        mechanic_id: str,
        created_by: str,
        client_id: str | None = None,
        template_id: str | None = None,
        mileage_at_inspection: int | None = None,
        fuel_level: str | None = None,
    ) -> Inspection:
        # Snapshots
        vehicle = await run_sync(self._vehicles.find_by_id, vehicle_id, tenant_id)
        if vehicle is None:
            raise NotFoundException(f"Vehículo '{vehicle_id}' no encontrado")

        client_snapshot: ClientSnapshot | None = None
        if client_id:
            client = await run_sync(self._clients.find_by_id, client_id, tenant_id)
            if client is not None:
                client_snapshot = ClientSnapshot(
                    id=client.id,
                    full_name=client.full_name,
                    email=client.email,
                    phone=client.phone,
                    rut=client.rut,
                )

        vehicle_snapshot = VehicleSnapshot(
            id=vehicle.id,
            plate=vehicle.plate,
            make=vehicle.make,
            model=vehicle.model,
            year=vehicle.year,
            color=vehicle.color,
            vin=vehicle.vin,
        )

        # Número correlativo
        year = datetime.now(timezone.utc).year
        number = await run_sync(self._counter.next_number, tenant_id, year)

        # Calcular total_items desde plantilla (0 si no hay plantilla)
        total_items = 0
        if template_id:
            template = await run_sync(self._templates.find_by_id, template_id)
            if template is not None:
                total_items = template.total_item_count

        now = datetime.now(timezone.utc)
        inspection_id = str(uuid.uuid4())
        inspection = Inspection(
            id=inspection_id,
            tenant_id=tenant_id,
            number=number,
            vehicle_id=vehicle_id,
            client_id=client_id,
            mechanic_id=mechanic_id,
            template_id=template_id,
            status=STATUS_DRAFT,
            vehicle_snapshot=vehicle_snapshot,
            client_snapshot=client_snapshot,
            mileage_at_inspection=mileage_at_inspection,
            fuel_level=fuel_level,
            total_items=total_items,
            good_items=0, regular_items=0, bad_items=0, na_items=0,
            score=None,
            total_repair_cost=0.0,
            currency="CLP",
            is_offline=False,
            created_at=now,
            updated_at=now,
            created_by=created_by,
            updated_by=created_by,
        )
        await run_sync(self._inspections.create, inspection)

        # Crear ítems desde la plantilla en batch
        if template_id:
            from functools import partial
            items = await run_sync(
                partial(_build_items_from_template, template_id, inspection_id, tenant_id, created_by),
                self._templates,
            )
            if items:
                await run_sync(self._items.create_batch, inspection_id, items)

        return inspection


class GetInspectionUseCase:
    def __init__(self, repo: InspectionRepository, item_repo: ItemRepository) -> None:
        self._repo = repo
        self._items = item_repo

    async def execute(
        self, inspection_id: str, tenant_id: str
    ) -> tuple[Inspection, list[InspectionItem]]:
        inspection = await run_sync(self._repo.find_by_id, inspection_id, tenant_id)
        if inspection is None:
            raise NotFoundException(f"Inspección '{inspection_id}' no encontrada")
        items = await run_sync(self._items.list_by_inspection, inspection_id)
        return inspection, items


class ListInspectionsUseCase:
    def __init__(self, repo: InspectionRepository) -> None:
        self._repo = repo

    async def execute(
        self,
        tenant_id: str,
        status: str | None = None,
        vehicle_id: str | None = None,
        mechanic_id: str | None = None,
    ) -> list[Inspection]:
        return await run_sync(
            self._repo.list_by_tenant, tenant_id, status, vehicle_id, mechanic_id
        )
