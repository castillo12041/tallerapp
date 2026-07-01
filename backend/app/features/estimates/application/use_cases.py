from __future__ import annotations

import uuid
from datetime import datetime, timezone

from app.core.exceptions import ConflictException, NotFoundException
from app.core.utils import run_sync
from app.features.estimates.domain.entities import Estimate, EstimateItem
from app.features.estimates.domain.workflow import STATUS_DRAFT
from app.features.estimates.infrastructure.counter_repository import (
    EstimateCounterRepository,
)
from app.features.estimates.infrastructure.estimate_repository import EstimateRepository
from app.features.estimates.infrastructure.item_repository import EstimateItemRepository
from app.features.inspections.infrastructure.inspection_repository import (
    InspectionRepository,
)
from app.features.vehicles.infrastructure.vehicle_repository import VehicleRepository


def _build_item_dict(
    item_data: dict,
    estimate_id: str,
    tenant_id: str,
    created_by: str,
) -> dict:
    now = datetime.now(timezone.utc)
    qty = float(item_data["quantity"])
    price = float(item_data["unit_price"])
    return {
        "id": str(uuid.uuid4()),
        "tenantId": tenant_id,
        "estimateId": estimate_id,
        "name": item_data["name"],
        "quantity": qty,
        "unitPrice": price,
        "subtotal": round(qty * price, 2),
        "category": item_data.get("category"),
        "description": item_data.get("description"),
        "inspectionItemId": item_data.get("inspection_item_id"),
        "createdAt": now,
        "updatedAt": now,
        "createdBy": created_by,
        "updatedBy": created_by,
    }


def _compute_totals(
    items: list[dict], tax_rate: float
) -> tuple[float, float, float]:
    subtotal = round(sum(i["subtotal"] for i in items), 2)
    tax_amount = round(subtotal * tax_rate, 2)
    total = round(subtotal + tax_amount, 2)
    return subtotal, tax_amount, total


class CreateEstimateUseCase:
    def __init__(
        self,
        estimate_repo: EstimateRepository,
        item_repo: EstimateItemRepository,
        counter_repo: EstimateCounterRepository,
        vehicle_repo: VehicleRepository,
        inspection_repo: InspectionRepository,
    ) -> None:
        self._estimates = estimate_repo
        self._items = item_repo
        self._counter = counter_repo
        self._vehicles = vehicle_repo
        self._inspections = inspection_repo

    async def execute(
        self,
        tenant_id: str,
        vehicle_id: str,
        created_by: str,
        items_data: list[dict],
        tax_rate: float = 0.19,
        inspection_id: str | None = None,
        notes: str | None = None,
        valid_until: datetime | None = None,
        currency: str = "CLP",
    ) -> Estimate:
        vehicle = await run_sync(self._vehicles.find_by_id, vehicle_id, tenant_id)
        if vehicle is None:
            raise NotFoundException(f"Vehículo '{vehicle_id}' no encontrado")

        client_snapshot = None
        if inspection_id:
            inspection = await run_sync(
                self._inspections.find_by_id, inspection_id, tenant_id
            )
            if inspection is None or inspection.tenant_id != tenant_id:
                raise NotFoundException(f"Inspección '{inspection_id}' no encontrada")
            client_snapshot = inspection.client_snapshot

        if not items_data:
            raise ConflictException("El presupuesto debe tener al menos un ítem")

        now = datetime.now(timezone.utc)
        estimate_id = str(uuid.uuid4())
        number = await run_sync(
            self._counter.next_number, tenant_id, now.year
        )

        item_dicts = [
            _build_item_dict(i, estimate_id, tenant_id, created_by) for i in items_data
        ]
        subtotal, tax_amount, total = _compute_totals(item_dicts, tax_rate)

        doc: dict = {
            "id": estimate_id,
            "tenantId": tenant_id,
            "number": number,
            "status": STATUS_DRAFT,
            "inspectionId": inspection_id,
            "vehicleSnapshot": {
                "id": vehicle.id,
                "plate": vehicle.plate,
                "make": vehicle.make,
                "model": vehicle.model,
                "year": getattr(vehicle, "year", None),
                "color": getattr(vehicle, "color", None),
                "vin": getattr(vehicle, "vin", None),
            },
            "clientSnapshot": {
                "id": client_snapshot.id,
                "fullName": client_snapshot.full_name,
                "email": client_snapshot.email,
                "phone": client_snapshot.phone,
                "rut": client_snapshot.rut,
            } if client_snapshot else None,
            "itemsCount": len(item_dicts),
            "subtotal": subtotal,
            "taxRate": tax_rate,
            "taxAmount": tax_amount,
            "total": total,
            "currency": currency,
            "notes": notes,
            "clientNotes": None,
            "publicTokenId": None,
            "validUntil": valid_until,
            "sentAt": None,
            "viewedAt": None,
            "respondedAt": None,
            "deletedAt": None,
            "createdAt": now,
            "updatedAt": now,
            "createdBy": created_by,
            "updatedBy": created_by,
        }

        await run_sync(self._estimates.create, doc)
        await run_sync(self._items.create_batch, estimate_id, item_dicts)
        return await run_sync(self._estimates.find_by_id, estimate_id, tenant_id)  # type: ignore[return-value]


class GetEstimateUseCase:
    def __init__(
        self,
        estimate_repo: EstimateRepository,
        item_repo: EstimateItemRepository,
    ) -> None:
        self._estimates = estimate_repo
        self._items = item_repo

    async def execute(
        self, tenant_id: str, estimate_id: str
    ) -> tuple[Estimate, list[EstimateItem]]:
        estimate = await run_sync(self._estimates.find_by_id, estimate_id, tenant_id)
        if estimate is None:
            raise NotFoundException(f"Presupuesto '{estimate_id}' no encontrado")
        items = await run_sync(self._items.list_by_estimate, estimate_id)
        return estimate, items


class ListEstimatesUseCase:
    def __init__(self, estimate_repo: EstimateRepository) -> None:
        self._estimates = estimate_repo

    async def execute(
        self,
        tenant_id: str,
        status: str | None = None,
        inspection_id: str | None = None,
    ) -> list[Estimate]:
        return await run_sync(
            self._estimates.list_by_tenant, tenant_id, status, inspection_id
        )


class UpdateEstimateUseCase:
    def __init__(self, estimate_repo: EstimateRepository) -> None:
        self._estimates = estimate_repo

    async def execute(
        self,
        tenant_id: str,
        estimate_id: str,
        updated_by: str,
        fields: dict,
    ) -> Estimate:
        estimate = await run_sync(self._estimates.find_by_id, estimate_id, tenant_id)
        if estimate is None:
            raise NotFoundException(f"Presupuesto '{estimate_id}' no encontrado")
        if estimate.status != STATUS_DRAFT:
            raise ConflictException(
                f"Solo se puede editar un presupuesto en estado '{STATUS_DRAFT}'. "
                f"Estado actual: '{estimate.status}'"
            )
        await run_sync(self._estimates.update, estimate_id, tenant_id, fields, updated_by)
        return await run_sync(self._estimates.find_by_id, estimate_id, tenant_id)  # type: ignore[return-value]


class DeleteEstimateUseCase:
    def __init__(self, estimate_repo: EstimateRepository) -> None:
        self._estimates = estimate_repo

    async def execute(self, tenant_id: str, estimate_id: str, deleted_by: str) -> None:
        estimate = await run_sync(self._estimates.find_by_id, estimate_id, tenant_id)
        if estimate is None:
            raise NotFoundException(f"Presupuesto '{estimate_id}' no encontrado")
        if estimate.status not in {STATUS_DRAFT}:
            raise ConflictException(
                "Solo se pueden eliminar presupuestos en estado 'draft'"
            )
        await run_sync(self._estimates.soft_delete, estimate_id, deleted_by)
