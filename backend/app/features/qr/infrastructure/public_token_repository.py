from __future__ import annotations

from datetime import datetime, timezone

from app.features.qr.domain.entities import PublicToken

_COL = "public_tokens"


def _to_entity(data: dict, doc_id: str) -> PublicToken:
    return PublicToken(
        id=doc_id,
        tenant_id=data["tenantId"],
        resource_id=data["resourceId"],
        token_type=data["tokenType"],
        issued_at=data["issuedAt"],
        expires_at=data["expiresAt"],
        revoked_at=data.get("revokedAt"),
        created_at=data["createdAt"],
        updated_at=data["updatedAt"],
        created_by=data["createdBy"],
        updated_by=data["updatedBy"],
    )


class PublicTokenRepository:
    def __init__(self, db: object) -> None:
        self._db = db  # firestore.Client

    def create(self, token: PublicToken) -> None:
        self._db.collection(_COL).document(token.id).set({  # type: ignore[union-attr]
            "tenantId": token.tenant_id,
            "resourceId": token.resource_id,
            "tokenType": token.token_type,
            "issuedAt": token.issued_at,
            "expiresAt": token.expires_at,
            "revokedAt": None,
            "createdAt": token.created_at,
            "updatedAt": token.updated_at,
            "createdBy": token.created_by,
            "updatedBy": token.updated_by,
        })

    def find_by_id(self, token_id: str) -> PublicToken | None:
        doc = self._db.collection(_COL).document(token_id).get()  # type: ignore[union-attr]
        if not doc.exists:
            return None
        return _to_entity(doc.to_dict(), doc.id)

    def revoke(self, token_id: str, revoked_by: str) -> None:
        now = datetime.now(timezone.utc)
        self._db.collection(_COL).document(token_id).update({  # type: ignore[union-attr]
            "revokedAt": now,
            "updatedAt": now,
            "updatedBy": revoked_by,
        })

    def list_by_resource(self, resource_id: str, tenant_id: str) -> list[PublicToken]:
        q = (
            self._db.collection(_COL)  # type: ignore[union-attr]
            .where("resourceId", "==", resource_id)
            .where("tenantId", "==", tenant_id)
        )
        return [_to_entity(d.to_dict(), d.id) for d in q.stream()]
