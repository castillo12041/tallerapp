from __future__ import annotations

import asyncio
import time
from collections import defaultdict

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.core.config import settings

# Endpoints de autenticación con límite más estricto
_AUTH_PATHS = {"/api/v1/auth/login", "/api/v1/auth/refresh", "/api/v1/auth/register"}


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiter de ventana deslizante por IP.

    IMPORTANTE: implementación en memoria — válida para un único proceso.
    En producción con múltiples workers, reemplazar por Redis con el paquete
    `slowapi` o `fastapi-limiter` para compartir estado entre procesos.
    """

    def __init__(self, app) -> None:
        super().__init__(app)
        self._requests: dict[str, list[float]] = defaultdict(list)
        self._lock = asyncio.Lock()

    async def dispatch(self, request: Request, call_next) -> Response:
        client_ip = request.client.host if request.client else "unknown"
        path = request.url.path

        is_auth_path = path in _AUTH_PATHS
        max_calls = settings.RATE_LIMIT_AUTH_CALLS if is_auth_path else settings.RATE_LIMIT_CALLS
        period = settings.RATE_LIMIT_PERIOD_SECONDS

        key = f"{'auth' if is_auth_path else 'api'}:{client_ip}"

        async with self._lock:
            now = time.monotonic()
            window_start = now - period
            self._requests[key] = [t for t in self._requests[key] if t > window_start]

            if len(self._requests[key]) >= max_calls:
                return JSONResponse(
                    status_code=429,
                    content={
                        "detail": "Demasiadas solicitudes. Intenta nuevamente más tarde.",
                        "error_code": "RATE_LIMIT_EXCEEDED",
                    },
                    headers={
                        "Retry-After": str(period),
                        "X-RateLimit-Limit": str(max_calls),
                        "X-RateLimit-Remaining": "0",
                        "X-RateLimit-Reset": str(int(now + period)),
                    },
                )

            self._requests[key].append(now)

        return await call_next(request)
