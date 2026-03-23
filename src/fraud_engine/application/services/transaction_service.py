from __future__ import annotations

import json
from datetime import datetime

import structlog
from ulid import ULID

from fraud_engine.application.dto import CreateTransactionDTO, TransactionResultDTO
from fraud_engine.application.ports import (
    AlertRepository,
    CachePort,
    CustomerRepository,
    EventBus,
    RuleRepository,
    StoragePort,
    TransactionRepository,
)
from fraud_engine.domain.engine import RuleEngine
from fraud_engine.domain.enums import AlertStatus
from fraud_engine.domain.models import FraudAlert, Transaction

logger = structlog.get_logger()


class TransactionService:
    def __init__(
        self,
        transaction_repo: TransactionRepository,
        rule_repo: RuleRepository,
        alert_repo: AlertRepository,
        customer_repo: CustomerRepository,
        event_bus: EventBus,
        cache: CachePort,
        storage: StoragePort,
    ) -> None:
        self._txn_repo = transaction_repo
        self._rule_repo = rule_repo
        self._alert_repo = alert_repo
        self._customer_repo = customer_repo
        self._event_bus = event_bus
        self._cache = cache
        self._storage = storage
        self._engine = RuleEngine()

    async def ingest(self, dto: CreateTransactionDTO, sync: bool = False) -> TransactionResultDTO:
        txn_id = str(ULID())
        now = datetime.utcnow()

        transaction = Transaction(
            id=txn_id,
            customer_id=dto.customer_id,
            amount=dto.amount,
            currency=dto.currency,
            merchant=dto.merchant,
            category=dto.category,
            channel=dto.channel,
            latitude=dto.latitude,
            longitude=dto.longitude,
            timestamp=dto.timestamp or now,
            card_number_hash=dto.card_number_hash,
            metadata=dto.metadata,
            created_at=now,
        )

        await self._txn_repo.save(transaction)
        logger.info("transaction_ingested", transaction_id=txn_id, customer_id=dto.customer_id)

        if sync:
            return await self.evaluate_transaction(transaction)

        # Async: publish to event bus
        await self._event_bus.publish(
            "TransactionReceived",
            {"transaction_id": txn_id, "customer_id": dto.customer_id, "amount": dto.amount},
        )

        return TransactionResultDTO(
            transaction_id=txn_id,
            is_flagged=False,
            alerts=[],
            composite_risk_score=0.0,
            severity="pending_evaluation",
        )

    async def evaluate_transaction(self, transaction: Transaction) -> TransactionResultDTO:
        rule_configs = await self._rule_repo.list_enabled()
        customer_profile = await self._customer_repo.get_profile(transaction.customer_id)
        recent_txns = await self._txn_repo.get_recent(transaction.customer_id)

        results = self._engine.evaluate(transaction, rule_configs, customer_profile, recent_txns)

        triggered = [r for r in results if r.triggered]
        composite_score = RuleEngine.compute_composite_score(results)
        severity = RuleEngine.determine_severity(composite_score)

        alerts: list[FraudAlert] = []
        for result in triggered:
            alert = FraudAlert(
                id=str(ULID()),
                transaction_id=transaction.id,
                customer_id=transaction.customer_id,
                rule_id=result.rule_id,
                rule_type=result.rule_type,
                risk_score=result.risk_score,
                severity=result.severity,
                description=result.description,
                details=result.details,
                status=AlertStatus.PENDING,
            )
            alerts.append(alert)

        if alerts:
            await self._alert_repo.save_many(alerts)
            await self._txn_repo.flag(transaction.id)

            # Publish fraud detected event
            await self._event_bus.publish(
                "FraudDetected",
                {
                    "transaction_id": transaction.id,
                    "customer_id": transaction.customer_id,
                    "alert_count": len(alerts),
                    "composite_risk_score": composite_score,
                    "severity": severity.value,
                },
            )

            # Store audit log
            audit_data = {
                "transaction_id": transaction.id,
                "customer_id": transaction.customer_id,
                "alerts": [
                    {"id": a.id, "rule_type": a.rule_type, "risk_score": a.risk_score}
                    for a in alerts
                ],
                "composite_score": composite_score,
                "timestamp": datetime.utcnow().isoformat(),
            }
            await self._storage.put(
                f"audit/alerts/{transaction.id}.json",
                json.dumps(audit_data).encode(),
            )

            logger.warning(
                "fraud_detected",
                transaction_id=transaction.id,
                alert_count=len(alerts),
                composite_score=composite_score,
            )

        return TransactionResultDTO(
            transaction_id=transaction.id,
            is_flagged=bool(alerts),
            alerts=[
                {
                    "id": a.id,
                    "rule_type": a.rule_type,
                    "severity": a.severity,
                    "description": a.description,
                    "risk_score": a.risk_score,
                }
                for a in alerts
            ],
            composite_risk_score=composite_score,
            severity=severity.value,
        )

    async def get_transaction(self, transaction_id: str) -> Transaction | None:
        return await self._txn_repo.get_by_id(transaction_id)

    async def list_transactions(
        self,
        customer_id: str | None = None,
        category: str | None = None,
        min_amount: float | None = None,
        max_amount: float | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        is_flagged: bool | None = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "timestamp",
        order: str = "desc",
    ) -> tuple[list[Transaction], int]:
        return await self._txn_repo.list(
            customer_id=customer_id,
            category=category,
            min_amount=min_amount,
            max_amount=max_amount,
            start_date=start_date,
            end_date=end_date,
            is_flagged=is_flagged,
            page=page,
            page_size=page_size,
            sort_by=sort_by,
            order=order,
        )
