"""
Configuración global de tests.

Parchea Firebase Admin SDK para que los tests corran sin credenciales reales.
Los tests de integración con Firestore/Auth usan el emulador de Firebase.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app

# Clave JWT compartida por todos los tests — 32+ caracteres, solo para testing.
JWT_TEST_SECRET = "test-secret-key-32-characters-long!!"


@pytest.fixture
def client() -> AsyncClient:
    """Cliente HTTP async apuntando a la app de tests."""
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


@pytest.fixture(autouse=True, scope="session")
def mock_firebase():
    """
    Reemplaza Firebase Admin SDK con mocks para todos los tests unitarios.
    Evita que `initialize_firebase()` en el lifespan de FastAPI falle
    por falta de firebase_credentials.json en el entorno de CI.
    """
    with (
        patch("app.core.firebase.firebase_admin") as mock_admin,
        patch("app.core.firebase.credentials") as mock_creds,
        patch("app.core.firebase.firestore") as mock_firestore,
        patch("app.core.firebase.auth") as mock_auth,
    ):
        mock_admin._apps = {}
        mock_admin.initialize_app.return_value = MagicMock()
        mock_creds.Certificate.return_value = MagicMock()
        mock_firestore.client.return_value = MagicMock()
        mock_auth.verify_id_token.return_value = {}

        yield {
            "admin": mock_admin,
            "credentials": mock_creds,
            "firestore": mock_firestore,
            "auth": mock_auth,
        }


@pytest.fixture(autouse=True)
def reset_rate_limiter() -> None:
    """
    Limpia el contador del rate limiter antes de cada test.
    Sin esto, los tests acumulan peticiones compartiendo la misma IP
    y los tests posteriores a ~60 requests reciben 429.
    """
    from app.middleware.rate_limit import RateLimitMiddleware

    node = app.middleware_stack
    while node is not None:
        if isinstance(node, RateLimitMiddleware):
            node._requests.clear()
            break
        node = getattr(node, "app", None)
