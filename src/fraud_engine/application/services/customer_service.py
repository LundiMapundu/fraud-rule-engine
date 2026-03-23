from __future__ import annotations

import json

import structlog

from fraud_engine.application.ports import (
    AlertRepository,
    CachePort,
    CustomerRepository,
    TransactionRepository,
)
from fraud_engine.domain.exceptions import CustomerNotFoundError
from fraud_engine.domain.models import CustomerRiskProfile, FraudAlert, Transaction

logger = structlog.get_logger()

PROFILE_CACHE_TTL = 300  # 5 minutes


class CustomerService:
    def __init__(
        self,
        customer_repo: CustomerRepository,
        transaction_repo: TransactionRepository,
        alert_repo: AlertRepository,
        cache: CachePort,
    ) -> None:
        self._customer_repo = customer_repo
        self._txn_repo = transaction_repo
        self._alert_repo = alert_repo
        self._cache = cache

    async def get_profile(self, customer_id: str) -> CustomerRiskProfile:
        # Try cache first
        cache_key = f"customer:profile:{customer_id}"
        cached = await self._cache.get(cache_key)
        if cached:
            data = json.loads(cached)
            return CustomerRiskProfile(**data)

        profile = await self._customer_repo.get_profile(customer_id)
        if profile is None:
            raise CustomerNotFoundError(customer_id)

        # Cache the profile
        profile_data = {
            "id": profile.id,
            "customer_id": profile.customer_id,
            "composite_risk_score": profile.composite_risk_score,
            "total_alerts": profile.total_alerts,
            "critical_alerts": profile.critical_alerts,
            "high_alerts": profile.high_alerts,
            "medium_alerts": profile.medium_alerts,
            "low_alerts": profile.low_alerts,
            "usual_categories": profile.usual_categories,
            "usual_locations": profile.usual_locations,
            "avg_transaction_amount": profile.avg_transaction_amount,
            "total_transactions": profile.total_transactions,
        }
        await self._cache.set(cache_key, json.dumps(profile_data), PROFILE_CACHE_TTL)

        return profile

    async def get_transactions(
        self, customer_id: str, page: int = 1, page_size: int = 20
    ) -> tuple[list[Transaction], int]:
        return await self._txn_repo.list(customer_id=customer_id, page=page, page_size=page_size)

    async def get_alerts(
        self, customer_id: str, page: int = 1, page_size: int = 20
    ) -> tuple[list[FraudAlert], int]:
        return await self._alert_repo.get_by_customer(
            customer_id=customer_id, page=page, page_size=page_size
        )
