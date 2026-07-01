"""
Genera números correlativos de inspección con transacción Firestore.

Formato: INS-{YEAR}-{NNNNNN}  (6 dígitos con cero izquierdo)
Contador almacenado en inspection_counters/{tenantId} con campos y{YEAR}.
"""

from __future__ import annotations

from firebase_admin import firestore as fb_fs

_COL = "inspection_counters"


class InspectionCounterRepository:
    def __init__(self, db) -> None:
        self._db = db

    def next_number(self, tenant_id: str, year: int) -> str:
        """
        Incrementa atómicamente el contador por tenant/año y retorna el número
        formateado. Seguro para múltiples workers concurrentes.
        """
        ref = self._db.collection(_COL).document(tenant_id)
        field = f"y{year}"

        @fb_fs.transactional
        def _run(txn, doc_ref):
            snap = doc_ref.get(transaction=txn)
            data = snap.to_dict() or {}
            new_val: int = data.get(field, 0) + 1
            txn.set(doc_ref, {field: new_val}, merge=True)
            return new_val

        count: int = _run(self._db.transaction(), ref)
        return f"INS-{year}-{count:06d}"
