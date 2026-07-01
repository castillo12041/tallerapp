"""
Utilidades compartidas para scripts de seed.
"""

from __future__ import annotations

import firebase_admin
from firebase_admin import credentials, firestore


def init_firebase(project_id: str) -> firestore.Client:
    """Inicializa Firebase Admin SDK con ApplicationDefault credentials.

    Idempotente: si ya está inicializado, retorna el cliente existente.
    Requiere GOOGLE_APPLICATION_CREDENTIALS apuntando al service account JSON.
    """
    if not firebase_admin._apps:
        cred = credentials.ApplicationDefault()
        firebase_admin.initialize_app(cred, {"projectId": project_id})
    return firestore.client()
