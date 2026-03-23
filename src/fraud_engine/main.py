from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

import structlog
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from fraud_engine.adapters.api.middleware import CorrelationIdMiddleware, domain_exception_to_status
from fraud_engine.adapters.api.v1 import alerts, analytics, customers, health, rules, transactions
from fraud_engine.adapters.cache.redis_cache import RedisCache
from fraud_engine.adapters.events.sqs_event_bus import SqsEventBus
from fraud_engine.adapters.storage.s3_client import S3StorageClient
from fraud_engine.config import settings
from fraud_engine.domain.exceptions import DomainError
from fraud_engine.observability.logging import setup_logging

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    setup_logging(
        log_level=settings.log_level,
        json_output=settings.is_production,
    )

    # Initialize adapters
    cache = RedisCache(settings.redis_url)
    event_bus = SqsEventBus(settings)
    storage = S3StorageClient(settings)

    app.state.cache = cache
    app.state.event_bus = event_bus
    app.state.storage = storage

    # Set up SQS consumer handler
    async def handle_event(event_type: str, payload: dict[str, Any]) -> None:
        if event_type == "TransactionReceived":
            from fraud_engine.adapters.persistence.database import async_session_factory
            from fraud_engine.adapters.persistence.repositories.alert_repo import (
                SqlAlchemyAlertRepository,
            )
            from fraud_engine.adapters.persistence.repositories.customer_repo import (
                SqlAlchemyCustomerRepository,
            )
            from fraud_engine.adapters.persistence.repositories.rule_repo import (
                SqlAlchemyRuleRepository,
            )
            from fraud_engine.adapters.persistence.repositories.transaction_repo import (
                SqlAlchemyTransactionRepository,
            )
            from fraud_engine.application.services.transaction_service import TransactionService

            async with async_session_factory() as session:
                try:
                    txn_repo = SqlAlchemyTransactionRepository(session)
                    txn = await txn_repo.get_by_id(payload["transaction_id"])
                    if txn is None:
                        logger.error(
                            "transaction_not_found_for_evaluation",
                            transaction_id=payload["transaction_id"],
                        )
                        return

                    svc = TransactionService(
                        transaction_repo=txn_repo,
                        rule_repo=SqlAlchemyRuleRepository(session),
                        alert_repo=SqlAlchemyAlertRepository(session),
                        customer_repo=SqlAlchemyCustomerRepository(session),
                        event_bus=event_bus,
                        cache=cache,
                        storage=storage,
                    )
                    await svc.evaluate_transaction(txn)
                    await session.commit()
                except Exception:
                    await session.rollback()
                    raise

    event_bus.set_handler(handle_event)

    if not settings.sync_mode:
        await event_bus.start_consuming()

    logger.info("app_started", env=settings.app_env)
    yield

    # Shutdown
    if not settings.sync_mode:
        await event_bus.stop_consuming()
    await cache.close()
    logger.info("app_stopped")


def create_app() -> FastAPI:
    app = FastAPI(
        title="Fraud Rule Engine",
        description="Real-time fraud detection service with configurable rules",
        version="1.0.0",
        lifespan=lifespan,
    )

    # Middleware
    app.add_middleware(CorrelationIdMiddleware)

    # Exception handlers
    @app.exception_handler(DomainError)
    async def domain_error_handler(request: Request, exc: DomainError) -> JSONResponse:
        status_code, body = domain_exception_to_status(exc)
        return JSONResponse(status_code=status_code, content=body)

    # Routes
    app.include_router(health.router)
    app.include_router(transactions.router, prefix="/api/v1")
    app.include_router(rules.router, prefix="/api/v1")
    app.include_router(alerts.router, prefix="/api/v1")
    app.include_router(analytics.router, prefix="/api/v1")
    app.include_router(customers.router, prefix="/api/v1")

    return app
