from __future__ import annotations

import structlog

from fraud_engine.domain.enums import RiskLevel
from fraud_engine.domain.models import CustomerRiskProfile, FraudRuleConfig, Transaction
from fraud_engine.domain.rules.base import EvaluationContext, RuleResult
from fraud_engine.domain.rules.registry import get_rule_instance

logger = structlog.get_logger()


class RuleEngine:
    """Orchestrator that evaluates all enabled rules against a transaction."""

    def evaluate(
        self,
        transaction: Transaction,
        rule_configs: list[FraudRuleConfig],
        customer_profile: CustomerRiskProfile | None,
        recent_transactions: list[Transaction],
    ) -> list[RuleResult]:
        results: list[RuleResult] = []

        for config in rule_configs:
            if not config.is_enabled:
                continue

            try:
                rule = get_rule_instance(config.rule_type)
                params = {**config.parameters, "rule_id": config.id}
                context = EvaluationContext(
                    transaction=transaction,
                    customer_profile=customer_profile,
                    recent_transactions=recent_transactions,
                    rule_parameters=params,
                )

                result = rule.evaluate(context)

                if result.triggered:
                    # Apply rule weight to the score
                    result.risk_score = min(1.0, result.risk_score * config.risk_weight)
                    result.severity = RuleResult.score_to_severity(result.risk_score)

                results.append(result)

            except Exception:
                logger.exception(
                    "rule_evaluation_failed",
                    rule_id=config.id,
                    rule_type=config.rule_type,
                )

        return results

    @staticmethod
    def compute_composite_score(results: list[RuleResult]) -> float:
        triggered = [r for r in results if r.triggered]
        if not triggered:
            return 0.0

        # Weighted average of triggered rule scores
        total = sum(r.risk_score for r in triggered)
        return min(1.0, total / len(triggered) + 0.1 * (len(triggered) - 1))

    @staticmethod
    def determine_severity(composite_score: float) -> RiskLevel:
        return RuleResult.score_to_severity(composite_score)
