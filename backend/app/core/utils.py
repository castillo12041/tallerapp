from __future__ import annotations

import asyncio
import hashlib
from collections.abc import Callable
from typing import TypeVar

T = TypeVar("T")


def hash_token(token: str) -> str:
    """SHA-256 del token en hexadecimal. Usar para almacenar refresh tokens en Firestore."""
    return hashlib.sha256(token.encode()).hexdigest()


async def run_sync(func: Callable[..., T], *args: object) -> T:
    """
    Ejecuta una función síncrona en el ThreadPoolExecutor por defecto.
    Necesario para llamar al Firebase Admin SDK (síncrono) desde código async.
    """
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, func, *args)
