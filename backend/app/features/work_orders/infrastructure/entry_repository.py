from __future__ import annotations

from app.features.work_orders.domain.entities import WorkOrderEntry

_COL = "work_orders"
_SUBCOL = "entries"


def _to_entity(data: dict, doc_id: str, work_order_id: str) -> WorkOrderEntry:
    return WorkOrderEntry(
        id=doc_id,
        tenant_id=data["tenantId"],
        work_order_id=work_order_id,
        entry_type=data["entryType"],
        from_status=data.get("fromStatus"),
        to_status=data.get("toStatus"),
        content=data.get("content"),
        created_at=data["createdAt"],
        created_by=data["createdBy"],
    )


class WorkOrderEntryRepository:
    def __init__(self, db: object) -> None:
        self._db = db

    def _subcol(self, work_order_id: str):  # type: ignore[return]
        return (
            self._db.collection(_COL)  # type: ignore[union-attr]
            .document(work_order_id)
            .collection(_SUBCOL)
        )

    def add(self, work_order_id: str, entry: dict) -> None:
        self._subcol(work_order_id).document(entry["id"]).set(entry)

    def list_by_work_order(self, work_order_id: str) -> list[WorkOrderEntry]:
        docs = (
            self._subcol(work_order_id)
            .order_by("createdAt", direction="ASCENDING")
            .stream()
        )
        return [_to_entity(d.to_dict(), d.id, work_order_id) for d in docs]
