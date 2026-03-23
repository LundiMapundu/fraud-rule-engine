from __future__ import annotations

import json
from datetime import datetime

import structlog
from ulid import ULID

from fraud_engine.application.dto import CreateRuleDTO, UpdateRuleDTO
from fraud_engine.application.ports import CachePort, RuleRepository, StoragePort
from fraud_engine.domain.exceptions import RuleNotFoundError
from fraud_engine.domain.models import FraudRuleConfig

logger = structlog.get_logger()


class RuleManagementService:
    def __init__(
        self,
        rule_repo: RuleRepository,
        cache: CachePort,
        storage: StoragePort,
    ) -> None:
        self._rule_repo = rule_repo
        self._cache = cache
        self._storage = storage

    async def create_rule(self, dto: CreateRuleDTO) -> FraudRuleConfig:
        rule = FraudRuleConfig(
            id=str(ULID()),
            name=dto.name,
            rule_type=dto.rule_type,
            is_enabled=dto.is_enabled,
            parameters=dto.parameters,
            risk_weight=dto.risk_weight,
            description=dto.description,
        )
        await self._rule_repo.save(rule)
        await self._cache.delete("rules:enabled")
        logger.info("rule_created", rule_id=rule.id, rule_type=rule.rule_type)
        return rule

    async def get_rule(self, rule_id: str) -> FraudRuleConfig:
        rule = await self._rule_repo.get_by_id(rule_id)
        if rule is None:
            raise RuleNotFoundError(rule_id)
        return rule

    async def list_rules(self) -> list[FraudRuleConfig]:
        return await self._rule_repo.list_all()

    async def update_rule(self, rule_id: str, dto: UpdateRuleDTO) -> FraudRuleConfig:
        rule = await self._rule_repo.get_by_id(rule_id)
        if rule is None:
            raise RuleNotFoundError(rule_id)

        if dto.name is not None:
            rule.name = dto.name
        if dto.parameters is not None:
            rule.parameters = dto.parameters
        if dto.risk_weight is not None:
            rule.risk_weight = dto.risk_weight
        if dto.is_enabled is not None:
            rule.is_enabled = dto.is_enabled
        if dto.description is not None:
            rule.description = dto.description
        rule.updated_at = datetime.utcnow()

        await self._rule_repo.update(rule)
        await self._cache.delete("rules:enabled")

        # Audit trail
        snapshot = {
            "rule_id": rule.id,
            "action": "updated",
            "changes": {k: v for k, v in vars(dto).items() if v is not None},
            "timestamp": datetime.utcnow().isoformat(),
        }
        await self._storage.put(
            f"audit/rules/{rule.id}/{datetime.utcnow().isoformat()}.json",
            json.dumps(snapshot).encode(),
        )

        logger.info("rule_updated", rule_id=rule_id)
        return rule

    async def delete_rule(self, rule_id: str) -> None:
        rule = await self._rule_repo.get_by_id(rule_id)
        if rule is None:
            raise RuleNotFoundError(rule_id)
        await self._rule_repo.delete(rule_id)
        await self._cache.delete("rules:enabled")
        logger.info("rule_deleted", rule_id=rule_id)
