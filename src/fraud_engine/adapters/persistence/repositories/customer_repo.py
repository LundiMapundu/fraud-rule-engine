from __future__ import annotations

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from fraud_engine.adapters.persistence.orm import CustomerRiskProfileModel
from fraud_engine.domain.models import CustomerRiskProfile


class SqlAlchemyCustomerRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _to_domain(self, model: CustomerRiskProfileModel) -> CustomerRiskProfile:
        return CustomerRiskProfile(
            id=model.id,
            customer_id=model.customer_id,
            composite_risk_score=model.composite_risk_score,
            total_alerts=model.total_alerts,
            critical_alerts=model.critical_alerts,
            high_alerts=model.high_alerts,
            medium_alerts=model.medium_alerts,
            low_alerts=model.low_alerts,
            usual_categories=model.usual_categories,
            usual_locations=model.usual_locations,
            avg_transaction_amount=model.avg_transaction_amount,
            total_transactions=model.total_transactions,
            updated_at=model.updated_at,
        )

    async def get_profile(self, customer_id: str) -> CustomerRiskProfile | None:
        result = await self._session.execute(
            select(CustomerRiskProfileModel).where(
                CustomerRiskProfileModel.customer_id == customer_id
            )
        )
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def upsert_profile(self, profile: CustomerRiskProfile) -> None:
        existing = await self._session.execute(
            select(CustomerRiskProfileModel).where(
                CustomerRiskProfileModel.customer_id == profile.customer_id
            )
        )
        model = existing.scalar_one_or_none()

        if model:
            model.composite_risk_score = profile.composite_risk_score
            model.total_alerts = profile.total_alerts
            model.critical_alerts = profile.critical_alerts
            model.high_alerts = profile.high_alerts
            model.medium_alerts = profile.medium_alerts
            model.low_alerts = profile.low_alerts
            model.usual_categories = profile.usual_categories
            model.usual_locations = profile.usual_locations
            model.avg_transaction_amount = profile.avg_transaction_amount
            model.total_transactions = profile.total_transactions
        else:
            model = CustomerRiskProfileModel(
                id=profile.id,
                customer_id=profile.customer_id,
                composite_risk_score=profile.composite_risk_score,
                total_alerts=profile.total_alerts,
                critical_alerts=profile.critical_alerts,
                high_alerts=profile.high_alerts,
                medium_alerts=profile.medium_alerts,
                low_alerts=profile.low_alerts,
                usual_categories=profile.usual_categories,
                usual_locations=profile.usual_locations,
                avg_transaction_amount=profile.avg_transaction_amount,
                total_transactions=profile.total_transactions,
            )
            self._session.add(model)

        await self._session.flush()

    async def get_high_risk(self, limit: int = 10) -> list[CustomerRiskProfile]:
        result = await self._session.execute(
            select(CustomerRiskProfileModel)
            .order_by(desc(CustomerRiskProfileModel.composite_risk_score))
            .limit(limit)
        )
        return [self._to_domain(m) for m in result.scalars().all()]
