"""
Números correlativos de presupuesto con transacción Firestore.
Formato: EST-{YEAR}-{NNNNNN}
Contador en estimate_counters/{tenantId} con campos y{YEAR}.
"""

from __future__ import annotations

from firebase_admin import firestore as fb_fs

_COL = "estimate_counters"


class EstimateCounterRepository:
    def __init__(self, db: object) -> None:
        self._db = db

    def next_number(self, tenant_id: str, year: int) -> str:
        ref = self._db.collection(_COL).document(tenant_id)  # type: ignore[union-attr]
        field = f"y{year}"

        @fb_fs.transactional
        def _run(txn, doc_ref):
            snap = doc_ref.get(transaction=txn)
            data = snap.to_dict() or {}
            new_val: int = data.get(field, 0) + 1
            txn.set(doc_ref, {field: new_val}, merge=True)
            return new_val

        count: int = _run(self._db.transaction(), ref)  # type: ignore[union-attr]
        return f"EST-{year}-{count:06d}"
