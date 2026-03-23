from __future__ import annotations

import hashlib
import hmac

from fastapi import HTTPException, Request, Security
from fastapi.security import APIKeyHeader

from fraud_engine.config import settings

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def _hash_key(key: str) -> str:
    return hashlib.sha256(key.encode()).hexdigest()


async def verify_api_key(
    request: Request,
    api_key: str | None = Security(api_key_header),
) -> str:
    # Skip auth for health checks
    if request.url.path in ("/health", "/health/ready", "/metrics"):
        return "anonymous"

    if api_key is None:
        raise HTTPException(status_code=401, detail="Missing API key")

    if not hmac.compare_digest(api_key, settings.api_key):
        raise HTTPException(status_code=403, detail="Invalid API key")

    return api_key
