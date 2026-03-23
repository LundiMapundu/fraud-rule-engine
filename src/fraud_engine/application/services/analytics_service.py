from __future__ import annotations

import structlog

from fraud_engine.application.ports import (
    AlertRepository,
    CustomerRepository,
    TransactionRepository,
)

logger = structlog.get_logger()


class AnalyticsService:
    def __init__(
        self,
        transaction_repo: TransactionRepository,
        alert_repo: AlertRepository,
        customer_repo: CustomerRepository,
    ) -> None:
        self._txn_repo = transaction_repo
        self._alert_repo = alert_repo
        self._customer_repo = customer_repo

    async def get_overview(self) -> dict:
        summary = await self._alert_repo.get_summary()
        return summary

    async def get_high_risk_customers(self, limit: int = 10) -> list:
        return await self._customer_repo.get_high_risk(limit=limit)
