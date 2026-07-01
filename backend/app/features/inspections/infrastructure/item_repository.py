from __future__ import annotations

from datetime import datetime, timezone

from app.features.inspections.domain.entities import InspectionItem

_INSPECTIONS_COL = "inspections"
_ITEMS_COL = "items"

_FIELD_MAP = {
    "status": "status",
    "observation": "observation",
    "repair_cost": "repairCost",
    "photo_urls": "photoUrls",
    "audio_url": "audioUrl",
}


def _to_entity(data: dict, doc_id: str, inspection_id: str) -> InspectionItem:
    raw_cre = data.get("createdAt")
    raw_upd = data.get("updatedAt")
    now = datetime.now(timezone.utc)
    photo_urls = data.get("photoUrls") or []
    return InspectionItem(
        id=doc_id,
        tenant_id=data.get("tenantId", ""),
        inspection_id=inspection_id,
        category=data.get("category", ""),
        category_order=data.get("categoryOrder", 0),
        name=data.get("name", ""),
        order=data.get("order", 0),
        status=data.get("status", "pending"),
        observation=data.get("observation"),
        repair_cost=data.get("repairCost"),
        photo_urls=tuple(photo_urls),
        audio_url=data.get("audioUrl"),
        photo_count=len(photo_urls),
        is_offline=data.get("isOffline", False),
        created_at=raw_cre if isinstance(raw_cre, datetime) else now,
        updated_at=raw_upd if isinstance(raw_upd, datetime) else now,
        created_by=data.get("createdBy", ""),
        updated_by=data.get("updatedBy", ""),
    )


def _items_col(db, inspection_id: str):
    return db.collection(_INSPECTIONS_COL).document(inspection_id).collection(_ITEMS_COL)


class ItemRepository:
    def __init__(self, db) -> None:
        self._db = db

    def create_batch(self, inspection_id: str, items: list[dict]) -> None:
        """Crea todos los ítems de una inspección en una sola escritura atómica."""
        if not items:
            return
        batch = self._db.batch()
        col = _items_col(self._db, inspection_id)
        for item in items:
            batch.set(col.document(item["id"]), item)
        batch.commit()

    def find_by_id(self, inspection_id: str, item_id: str) -> InspectionItem | None:
        doc = _items_col(self._db, inspection_id).document(item_id).get()
        if not doc.exists:
            return None
        return _to_entity(doc.to_dict(), doc.id, inspection_id)

    def list_by_inspection(self, inspection_id: str) -> list[InspectionItem]:
        docs = (
            _items_col(self._db, inspection_id)
            .order_by("categoryOrder")
            .order_by("order")
            .stream()
        )
        return [_to_entity(d.to_dict(), d.id, inspection_id) for d in docs]

    def update(self, inspection_id: str, item_id: str, fields: dict, updated_by: str) -> None:
        mapped: dict = {"updatedAt": datetime.now(timezone.utc), "updatedBy": updated_by}
        for py_key, fs_key in _FIELD_MAP.items():
            if py_key in fields:
                val = fields[py_key]
                mapped[fs_key] = val
                if py_key == "photo_urls":
                    mapped["photoCount"] = len(val) if val else 0
        _items_col(self._db, inspection_id).document(item_id).update(mapped)

    def count_statuses(self, inspection_id: str) -> dict[str, int]:
        """Returns {good, regular, bad, na, pending} counts for all items."""
        counts: dict[str, int] = {"good": 0, "regular": 0, "bad": 0, "na": 0, "pending": 0}
        total_repair = 0.0
        for doc in _items_col(self._db, inspection_id).stream():
            data = doc.to_dict()
            status = data.get("status", "pending")
            counts[status] = counts.get(status, 0) + 1
            if status == "bad" and data.get("repairCost"):
                total_repair += float(data["repairCost"])
        counts["total_repair_cost"] = total_repair  # type: ignore[assignment]
        return counts
