from __future__ import annotations

from fastapi import APIRouter, Request
from prometheus_client import generate_latest
from starlette.responses import Response

router = APIRouter(tags=["Health"])


@router.get("/health")
async def liveness():
    return {"status": "ok"}


@router.get("/health/ready")
async def readiness(request: Request):
    checks: dict[str, str] = {}

    # Database check
    try:
        import sqlalchemy

        from fraud_engine.adapters.persistence.database import engine

        async with engine.connect() as conn:
            await conn.execute(sqlalchemy.text("SELECT 1"))
        checks["database"] = "ok"
    except Exception as e:
        checks["database"] = f"error: {e}"

    # Redis check
    try:
        cache = request.app.state.cache
        await cache.set("health_check", "ok", ttl_seconds=5)
        checks["redis"] = "ok"
    except Exception as e:
        checks["redis"] = f"error: {e}"

    all_ok = all(v == "ok" for v in checks.values())
    status_code = 200 if all_ok else 503

    import json

    body = {"status": "ready" if all_ok else "degraded", "checks": checks}
    return Response(
        content=json.dumps(body),
        status_code=status_code,
        media_type="application/json",
    )


@router.get("/metrics")
async def metrics():
    return Response(content=generate_latest(), media_type="text/plain; charset=utf-8")
