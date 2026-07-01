from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from firebase_admin import firestore


@dataclass(frozen=True)
class RefreshTokenRecord:
    family_id: str
    token_hash: str
    user_id: str
    tenant_id: str | None
    is_revoked: bool
    expires_at: datetime
    revoked_at: datetime | None

    def matches(self, provided_hash: str) -> bool:
        return self.token_hash == provided_hash

    def is_valid(self) -> bool:
        return not self.is_revoked and datetime.now(timezone.utc) < self.expires_at


class RefreshTokenRepository:
    """
    Gestiona el ciclo de vida de los refresh tokens en Firestore.

    Colección: refresh_tokens/{family_id}

    La estrategia de rotación por familias detecta el reuso de tokens:
    si un token ya rotado se presenta de nuevo, se revoca toda la familia,
    forzando al usuario a volver a autenticarse con su proveedor de identidad.
    """

    _COLLECTION = "refresh_tokens"

    def __init__(self, db: firestore.Client) -> None:
        self._db = db

    def create(
        self,
        family_id: str,
        token_hash: str,
        user_id: str,
        tenant_id: str | None,
        expires_at: datetime,
    ) -> None:
        now = datetime.now(timezone.utc)
        self._db.collection(self._COLLECTION).document(family_id).set({
            "familyId": family_id,
            "tokenHash": token_hash,
            "userId": user_id,
            "tenantId": tenant_id,
            "isRevoked": False,
            "expiresAt": expires_at,
            "revokedAt": None,
            "createdAt": now,
            "updatedAt": now,
            "createdBy": user_id,
            "updatedBy": user_id,
        })

    def find_by_family(self, family_id: str) -> RefreshTokenRecord | None:
        doc = self._db.collection(self._COLLECTION).document(family_id).get()
        if not doc.exists:
            return None
        return self._to_record(doc.to_dict() or {})

    def rotate(
        self,
        family_id: str,
        new_token_hash: str,
        new_expires_at: datetime,
        user_id: str,
    ) -> None:
        now = datetime.now(timezone.utc)
        self._db.collection(self._COLLECTION).document(family_id).update({
            "tokenHash": new_token_hash,
            "expiresAt": new_expires_at,
            "updatedAt": now,
            "updatedBy": user_id,
        })

    def revoke_family(self, family_id: str, user_id: str | None = None) -> None:
        now = datetime.now(timezone.utc)
        self._db.collection(self._COLLECTION).document(family_id).update({
            "isRevoked": True,
            "revokedAt": now,
            "updatedAt": now,
            "updatedBy": user_id or "system",
        })

    def _to_record(self, data: dict) -> RefreshTokenRecord:
        expires_at = data.get("expiresAt")
        if isinstance(expires_at, datetime) and expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)

        revoked_at = data.get("revokedAt")
        if isinstance(revoked_at, datetime) and revoked_at.tzinfo is None:
            revoked_at = revoked_at.replace(tzinfo=timezone.utc)

        return RefreshTokenRecord(
            family_id=data.get("familyId", ""),
            token_hash=data.get("tokenHash", ""),
            user_id=data.get("userId", ""),
            tenant_id=data.get("tenantId") or None,
            is_revoked=bool(data.get("isRevoked", False)),
            expires_at=expires_at or datetime.now(timezone.utc),
            revoked_at=revoked_at,
        )
