"""
Singleton del Firebase Admin SDK.

Inicializado una vez en el lifespan de la aplicación.
Provee acceso a Firestore y Firebase Auth.

NOTA: firebase-admin Python SDK es síncrono. Para usarlo desde código async,
los callers deben ejecutar estas funciones en un ThreadPoolExecutor.
La abstracción async se implementa en la capa de servicios (Fase 4+).
"""

from __future__ import annotations

import firebase_admin
from firebase_admin import auth, credentials, firestore

from app.core.config import settings

_firestore_client: firestore.Client | None = None


def initialize_firebase() -> None:
    """Inicializa Firebase Admin SDK. Idempotente — llamar una sola vez en el lifespan."""
    if firebase_admin._apps:
        return

    cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)
    firebase_admin.initialize_app(
        cred,
        {"projectId": settings.FIREBASE_PROJECT_ID},
    )


def get_firestore() -> firestore.Client:
    """Retorna el cliente de Firestore (singleton)."""
    global _firestore_client
    if _firestore_client is None:
        _firestore_client = firestore.client()
    return _firestore_client


def verify_firebase_id_token(id_token: str) -> dict:
    """
    Verifica un Firebase ID Token y retorna sus claims.
    Síncrono — debe ejecutarse en un executor desde código async.
    Lanza firebase_admin.auth.InvalidIdTokenError si el token es inválido.
    """
    return auth.verify_id_token(id_token, check_revoked=True)


def set_custom_claims(uid: str, claims: dict) -> None:
    """
    Escribe custom claims en el Firebase Auth token del usuario.
    Síncrono — debe ejecutarse en un executor desde código async.
    Los claims se incluyen en el próximo ID token que emita Firebase.
    """
    auth.set_custom_user_claims(uid, claims)
