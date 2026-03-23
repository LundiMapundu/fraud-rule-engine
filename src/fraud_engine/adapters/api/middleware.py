from __future__ import annotations

import time
from typing import Any

import structlog
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from ulid import ULID

from fraud_engine.domain.exceptions import (
    AlertNotFoundError,
    CustomerNotFoundError,
    DomainError,
    RuleNotFoundError,
    TransactionNotFoundError,
)

logger = structlog.get_logger()

NOT_FOUND_EXCEPTIONS = (
    TransactionNotFoundError,
    RuleNotFoundError,
    AlertNotFoundError,
    CustomerNotFoundError,
)


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        correlation_id = request.headers.get("X-Correlation-ID", str(ULID()))
        request.state.correlation_id = correlation_id

        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(correlation_id=correlation_id)

        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = (time.perf_counter() - start) * 1000

        response.headers["X-Correlation-ID"] = correlation_id
        response.headers["X-Response-Time-Ms"] = f"{duration_ms:.1f}"

        logger.info(
            "request_completed",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=round(duration_ms, 1),
        )

        return response


def domain_exception_to_status(exc: DomainError) -> tuple[int, dict[str, Any]]:
    if isinstance(exc, NOT_FOUND_EXCEPTIONS):
        return 404, {"detail": str(exc)}
    return 400, {"detail": str(exc)}
