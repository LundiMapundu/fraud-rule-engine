from __future__ import annotations

from typing import Any

from sqlalchemy import Select, desc, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from fraud_engine.adapters.persistence.orm import FraudAlertModel
from fraud_engine.domain.enums import AlertStatus, RiskLevel, RuleType
from fraud_engine.domain.models import FraudAlert


class SqlAlchemyAlertRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _to_domain(self, model: FraudAlertModel) -> FraudAlert:
        return FraudAlert(
            id=model.id,
            transaction_id=model.transaction_id,
            customer_id=model.customer_id,
            rule_id=model.rule_id,
            rule_type=RuleType(model.rule_type),
            risk_score=model.risk_score,
            severity=RiskLevel(model.severity),
            description=model.description,
            details=model.details,
            status=AlertStatus(model.status),
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    async def save(self, alert: FraudAlert) -> None:
        model = FraudAlertModel(
            id=alert.id,
            transaction_id=alert.transaction_id,
            customer_id=alert.customer_id,
            rule_id=alert.rule_id,
            rule_type=alert.rule_type.value,
            risk_score=alert.risk_score,
            severity=alert.severity.value,
            description=alert.description,
            details=alert.details,
            status=alert.status.value,
        )
        self._session.add(model)
        await self._session.flush()

    async def save_many(self, alerts: list[FraudAlert]) -> None:
        for alert in alerts:
            await self.save(alert)

    async def get_by_id(self, alert_id: str) -> FraudAlert | None:
        result = await self._session.get(FraudAlertModel, alert_id)
        return self._to_domain(result) if result else None

    async def list(
        self,
        status: AlertStatus | None = None,
        severity: RiskLevel | None = None,
        customer_id: str | None = None,
        rule_type: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "created_at",
        order: str = "desc",
    ) -> tuple[list[FraudAlert], int]:
        query: Select = select(FraudAlertModel)  # type: ignore[type-arg]
        count_query = select(func.count()).select_from(FraudAlertModel)

        if status:
            query = query.where(FraudAlertModel.status == status.value)
            count_query = count_query.where(FraudAlertModel.status == status.value)
        if severity:
            query = query.where(FraudAlertModel.severity == severity.value)
            count_query = count_query.where(FraudAlertModel.severity == severity.value)
        if customer_id:
            query = query.where(FraudAlertModel.customer_id == customer_id)
            count_query = count_query.where(FraudAlertModel.customer_id == customer_id)
        if rule_type:
            query = query.where(FraudAlertModel.rule_type == rule_type)
            count_query = count_query.where(FraudAlertModel.rule_type == rule_type)
        if start_date:
            query = query.where(FraudAlertModel.created_at >= start_date)
            count_query = count_query.where(FraudAlertModel.created_at >= start_date)
        if end_date:
            query = query.where(FraudAlertModel.created_at <= end_date)
            count_query = count_query.where(FraudAlertModel.created_at <= end_date)

        sort_col = getattr(FraudAlertModel, sort_by, FraudAlertModel.created_at)
        query = query.order_by(desc(sort_col) if order == "desc" else sort_col)

        total_result = await self._session.execute(count_query)
        total = total_result.scalar() or 0

        offset = (page - 1) * page_size
        result = await self._session.execute(query.offset(offset).limit(page_size))
        return [self._to_domain(m) for m in result.scalars().all()], total

    async def update_status(self, alert_id: str, status: AlertStatus) -> None:
        stmt = (
            update(FraudAlertModel)
            .where(FraudAlertModel.id == alert_id)
            .values(status=status.value)
        )
        await self._session.execute(stmt)
        await self._session.flush()

    async def get_by_transaction(self, transaction_id: str) -> list[FraudAlert]:
        result = await self._session.execute(
            select(FraudAlertModel).where(FraudAlertModel.transaction_id == transaction_id)
        )
        return [self._to_domain(m) for m in result.scalars().all()]

    async def get_summary(self) -> dict[str, Any]:
        # Alerts by severity
        severity_result = await self._session.execute(
            select(FraudAlertModel.severity, func.count()).group_by(FraudAlertModel.severity)
        )
        by_severity = dict(severity_result.all())

        # Alerts by status
        status_result = await self._session.execute(
            select(FraudAlertModel.status, func.count()).group_by(FraudAlertModel.status)
        )
        by_status = dict(status_result.all())

        # Total and avg risk score
        stats_result = await self._session.execute(
            select(func.count(), func.coalesce(func.avg(FraudAlertModel.risk_score), 0))
        )
        row = stats_result.one()
        total = row[0]
        avg_score = float(row[1])

        return {
            "total_alerts": total,
            "alerts_by_severity": by_severity,
            "alerts_by_status": by_status,
            "avg_risk_score": round(avg_score, 3),
        }

    async def get_by_customer(
        self, customer_id: str, page: int = 1, page_size: int = 20
    ) -> tuple[list[FraudAlert], int]:
        return await self.list(customer_id=customer_id, page=page, page_size=page_size)
