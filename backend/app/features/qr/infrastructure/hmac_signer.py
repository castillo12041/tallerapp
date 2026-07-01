from __future__ import annotations

import base64
import hashlib
import hmac
import json


def _canonical(
    resource_id: str,
    tenant_id: str,
    token_id: str,
    iat: int,
    exp: int,
) -> str:
    return f"{resource_id}:{tenant_id}:{token_id}:{iat}:{exp}"


def _sign(canonical: str, secret: str) -> str:
    return hmac.new(
        secret.encode(), canonical.encode(), hashlib.sha256
    ).hexdigest()


def encode_token(
    resource_id: str,
    tenant_id: str,
    token_id: str,
    iat: int,
    exp: int,
    secret: str,
) -> str:
    """Construye y firma el payload; retorna base64url sin padding."""
    sig = _sign(_canonical(resource_id, tenant_id, token_id, iat, exp), secret)
    payload = {
        "iid": resource_id,
        "tid": tenant_id,
        "jti": token_id,
        "iat": iat,
        "exp": exp,
        "sig": sig,
    }
    json_bytes = json.dumps(payload, separators=(",", ":")).encode()
    return base64.urlsafe_b64encode(json_bytes).decode().rstrip("=")


def decode_and_verify_token(
    token: str,
    secret: str,
) -> dict | None:
    """
    Decodifica y verifica la firma HMAC del token.
    Retorna el payload si es válido, None si la firma no coincide o el token es malformado.
    La comparación es constant-time (no vulnerable a timing attacks).
    """
    try:
        padded = token + "=" * (4 - len(token) % 4)
        json_bytes = base64.urlsafe_b64decode(padded)
        payload = json.loads(json_bytes)
    except Exception:
        return None

    required = {"iid", "tid", "jti", "iat", "exp", "sig"}
    if not required.issubset(payload.keys()):
        return None

    expected_sig = _sign(
        _canonical(
            payload["iid"],
            payload["tid"],
            payload["jti"],
            payload["iat"],
            payload["exp"],
        ),
        secret,
    )
    if not hmac.compare_digest(expected_sig, payload["sig"]):
        return None

    return payload
