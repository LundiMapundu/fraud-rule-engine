from __future__ import annotations

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from fraud_engine.adapters.persistence.orm import FraudRuleConfigModel
from fraud_engine.domain.enums import RuleType
from fraud_engine.domain.models import FraudRuleConfig


class SqlAlchemyRuleRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _to_domain(self, model: FraudRuleConfigModel) -> FraudRuleConfig:
        return FraudRuleConfig(
            id=model.id,
            name=model.name,
            rule_type=RuleType(model.rule_type),
            is_enabled=model.is_enabled,
            parameters=model.parameters,
            risk_weight=model.risk_weight,
            description=model.description,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    async def save(self, rule: FraudRuleConfig) -> None:
        model = FraudRuleConfigModel(
            id=rule.id,
            name=rule.name,
            rule_type=rule.rule_type.value,
            is_enabled=rule.is_enabled,
            parameters=rule.parameters,
            risk_weight=rule.risk_weight,
            description=rule.description,
        )
        self._session.add(model)
        await self._session.flush()

    async def get_by_id(self, rule_id: str) -> FraudRuleConfig | None:
        result = await self._session.get(FraudRuleConfigModel, rule_id)
        return self._to_domain(result) if result else None

    async def list_all(self) -> list[FraudRuleConfig]:
        result = await self._session.execute(select(FraudRuleConfigModel))
        return [self._to_domain(m) for m in result.scalars().all()]

    async def list_enabled(self) -> list[FraudRuleConfig]:
        result = await self._session.execute(
            select(FraudRuleConfigModel).where(FraudRuleConfigModel.is_enabled.is_(True))
        )
        return [self._to_domain(m) for m in result.scalars().all()]

    async def update(self, rule: FraudRuleConfig) -> None:
        stmt = (
            update(FraudRuleConfigModel)
            .where(FraudRuleConfigModel.id == rule.id)
            .values(
                name=rule.name,
                is_enabled=rule.is_enabled,
                parameters=rule.parameters,
                risk_weight=rule.risk_weight,
                description=rule.description,
            )
        )
        await self._session.execute(stmt)
        await self._session.flush()

    async def delete(self, rule_id: str) -> None:
        await self._session.execute(
            delete(FraudRuleConfigModel).where(FraudRuleConfigModel.id == rule_id)
        )
        await self._session.flush()
