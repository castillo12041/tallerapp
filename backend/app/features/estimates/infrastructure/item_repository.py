from __future__ import annotations

from datetime import datetime, timezone

from app.features.estimates.domain.entities import EstimateItem

_COL = "estimates"
_SUBCOL = "items"


def _to_entity(data: dict, doc_id: str, estimate_id: str) -> EstimateItem:
    return EstimateItem(
        id=doc_id,
        tenant_id=data["tenantId"],
        estimate_id=estimate_id,
        name=data["name"],
        quantity=data["quantity"],
        unit_price=data["unitPrice"],
        subtotal=data["subtotal"],
        category=data.get("category"),
        description=data.get("description"),
        inspection_item_id=data.get("inspectionItemId"),
        created_at=data["createdAt"],
        updated_at=data["updatedAt"],
        created_by=data["createdBy"],
        updated_by=data["updatedBy"],
    )


class EstimateItemRepository:
    def __init__(self, db: object) -> None:
        self._db = db

    def create_batch(self, estimate_id: str, items: list[dict]) -> None:
        batch = self._db.batch()  # type: ignore[union-attr]
        col = self._db.collection(_COL).document(estimate_id).collection(_SUBCOL)  # type: ignore[union-attr]
        for item in items:
            ref = col.document(item["id"])
            batch.set(ref, item)
        batch.commit()

    def add_item(self, estimate_id: str, item: dict) -> None:
        self._db.collection(_COL).document(estimate_id).collection(_SUBCOL).document(  # type: ignore[union-attr]
            item["id"]
        ).set(item)

    def find_by_id(self, estimate_id: str, item_id: str) -> EstimateItem | None:
        doc = (
            self._db.collection(_COL).document(estimate_id)  # type: ignore[union-attr]
            .collection(_SUBCOL).document(item_id).get()
        )
        if not doc.exists:
            return None
        return _to_entity(doc.to_dict(), doc.id, estimate_id)

    def list_by_estimate(self, estimate_id: str) -> list[EstimateItem]:
        docs = (
            self._db.collection(_COL).document(estimate_id)  # type: ignore[union-attr]
            .collection(_SUBCOL)
            .order_by("category")
            .order_by("name")
            .stream()
        )
        return [_to_entity(d.to_dict(), d.id, estimate_id) for d in docs]

    def update(self, estimate_id: str, item_id: str, fields: dict, updated_by: str) -> None:
        now = datetime.now(timezone.utc)
        mapped: dict = {"updatedAt": now, "updatedBy": updated_by}
        for key in ("name", "description", "category"):
            if key in fields:
                mapped[key] = fields[key]
        if "quantity" in fields or "unit_price" in fields:
            # Necesitamos ambos valores para recalcular subtotal
            doc = self.find_by_id(estimate_id, item_id)
            qty = fields.get("quantity", doc.quantity if doc else 1)
            price = fields.get("unit_price", doc.unit_price if doc else 0)
            mapped["quantity"] = qty
            mapped["unitPrice"] = price
            mapped["subtotal"] = round(qty * price, 2)
        (
            self._db.collection(_COL).document(estimate_id)  # type: ignore[union-attr]
            .collection(_SUBCOL).document(item_id).update(mapped)
        )

    def delete(self, estimate_id: str, item_id: str) -> None:
        (
            self._db.collection(_COL).document(estimate_id)  # type: ignore[union-attr]
            .collection(_SUBCOL).document(item_id).delete()
        )

    def sum_subtotals(self, estimate_id: str) -> float:
        docs = (
            self._db.collection(_COL).document(estimate_id)  # type: ignore[union-attr]
            .collection(_SUBCOL).stream()
        )
        return round(sum(d.to_dict().get("subtotal", 0.0) for d in docs), 2)

    def count(self, estimate_id: str) -> int:
        docs = list(
            self._db.collection(_COL).document(estimate_id)  # type: ignore[union-attr]
            .collection(_SUBCOL).stream()
        )
        return len(docs)
