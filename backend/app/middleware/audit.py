from __future__ import annotations

import asyncio
import time
from datetime import datetime, timezone

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

_MUTATING_METHODS = frozenset({"POST", "PUT", "PATCH", "DELETE"})
_EXCLUDED_PATHS = frozenset({
    "/health",
    "/docs",
    "/redoc",
    "/openapi.json",
    "/api/v1/health",
    "/api/v2/health",
})


class AuditMiddleware(BaseHTTPMiddleware):
    """
    Registra en Firestore todas las mutaciones autenticadas (POST, PUT, PATCH, DELETE).

    Los datos before/after de cada documento se añaden desde la capa de servicio;
    este middleware solo captura el contexto de la request (usuario, ruta, status, duración).

    La escritura en Firestore corre en un ThreadPoolExecutor para no bloquear el event loop.
    Nunca interrumpe el flujo: los errores de escritura se ignoran silenciosamente.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        if request.method not in _MUTATING_METHODS or request.url.path in _EXCLUDED_PATHS:
            return await call_next(request)

        start = time.monotonic()
        response = await call_next(request)
        duration_ms = int((time.monotonic() - start) * 1000)

        user_id: str | None = getattr(request.state, "user_id", None)
        tenant_id: str | None = getattr(request.state, "tenant_id", None)

        if user_id and response.status_code < 500:
            audit_data = {
                "user_id": user_id,
                "tenant_id": tenant_id,
                "method": request.method,
                "path": str(request.url.path),
                "status_code": response.status_code,
                "duration_ms": duration_ms,
                "ip_address": request.client.host if request.client else None,
                "user_agent": request.headers.get("user-agent"),
            }
            loop = asyncio.get_running_loop()
            loop.run_in_executor(None, self._write_audit_log, audit_data)

        return response

    def _write_audit_log(self, data: dict) -> None:
        try:
            from app.core.firebase import get_firestore

            now = datetime.now(timezone.utc)
            db = get_firestore()
            db.collection("audit_logs").add({
                "tenantId": data["tenant_id"],
                "userId": data["user_id"],
                "action": data["method"],
                "path": data["path"],
                "statusCode": data["status_code"],
                "durationMs": data["duration_ms"],
                "ipAddress": data["ip_address"],
                "userAgent": data["user_agent"],
                "createdAt": now,
                "updatedAt": now,
                "createdBy": data["user_id"],
                "updatedBy": data["user_id"],
            })
        except Exception:
            pass
