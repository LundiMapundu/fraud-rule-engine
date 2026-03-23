from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from fraud_engine.adapters.api.auth import verify_api_key
from fraud_engine.adapters.cache.redis_cache import RedisCache
from fraud_engine.adapters.persistence.database import get_session
from fraud_engine.adapters.persistence.repositories.alert_repo import SqlAlchemyAlertRepository
from fraud_engine.adapters.persistence.repositories.customer_repo import (
    SqlAlchemyCustomerRepository,
)
from fraud_engine.adapters.persistence.repositories.rule_repo import SqlAlchemyRuleRepository
from fraud_engine.adapters.persistence.repositories.transaction_repo import (
    SqlAlchemyTransactionRepository,
)
from fraud_engine.adapters.storage.s3_client import S3StorageClient
from fraud_engine.application.services.analytics_service import AnalyticsService
from fraud_engine.application.services.customer_service import CustomerService
from fraud_engine.application.services.rule_management_service import RuleManagementService
from fraud_engine.application.services.transaction_service import TransactionService

AuthDep = Annotated[str, Depends(verify_api_key)]
SessionDep = Annotated[AsyncSession, Depends(get_session)]


def get_event_bus(request: Request):  # type: ignore[no-untyped-def]
    return request.app.state.event_bus


def get_cache(request: Request) -> RedisCache:
    return request.app.state.cache


def get_storage(request: Request) -> S3StorageClient:
    return request.app.state.storage


def get_transaction_service(
    session: SessionDep,
    request: Request,
) -> TransactionService:
    return TransactionService(
        transaction_repo=SqlAlchemyTransactionRepository(session),
        rule_repo=SqlAlchemyRuleRepository(session),
        alert_repo=SqlAlchemyAlertRepository(session),
        customer_repo=SqlAlchemyCustomerRepository(session),
        event_bus=get_event_bus(request),
        cache=get_cache(request),
        storage=get_storage(request),
    )


def get_rule_service(
    session: SessionDep,
    request: Request,
) -> RuleManagementService:
    return RuleManagementService(
        rule_repo=SqlAlchemyRuleRepository(session),
        cache=get_cache(request),
        storage=get_storage(request),
    )


def get_alert_repo(session: SessionDep) -> SqlAlchemyAlertRepository:
    return SqlAlchemyAlertRepository(session)


def get_analytics_service(session: SessionDep) -> AnalyticsService:
    return AnalyticsService(
        transaction_repo=SqlAlchemyTransactionRepository(session),
        alert_repo=SqlAlchemyAlertRepository(session),
        customer_repo=SqlAlchemyCustomerRepository(session),
    )


def get_customer_service(
    session: SessionDep,
    request: Request,
) -> CustomerService:
    return CustomerService(
        customer_repo=SqlAlchemyCustomerRepository(session),
        transaction_repo=SqlAlchemyTransactionRepository(session),
        alert_repo=SqlAlchemyAlertRepository(session),
        cache=get_cache(request),
    )
