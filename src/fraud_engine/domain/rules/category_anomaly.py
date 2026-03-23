from __future__ import annotations

from fraud_engine.domain.enums import RuleType
from fraud_engine.domain.rules.base import EvaluationContext, RuleResult


class CategoryAnomalyRule:
    """Flags transactions in categories the customer has never or rarely used."""

    rule_type = RuleType.CATEGORY_ANOMALY

    def evaluate(self, context: EvaluationContext) -> RuleResult:
        txn = context.transaction
        profile = context.customer_profile

        usual_categories: list[str] = []
        if profile and profile.usual_categories:
            usual_categories = profile.usual_categories

        # If no profile or no history, can't determine anomaly
        if not usual_categories:
            return RuleResult(
                rule_type=self.rule_type,
                rule_id=context.rule_parameters.get("rule_id", ""),
                triggered=False,
                risk_score=0.0,
                severity=RuleResult.score_to_severity(0.0),
                description="Insufficient history for category anomaly detection",
            )

        category = txn.category.value

        if category in usual_categories:
            return RuleResult(
                rule_type=self.rule_type,
                rule_id=context.rule_parameters.get("rule_id", ""),
                triggered=False,
                risk_score=0.0,
                severity=RuleResult.score_to_severity(0.0),
                description=f"Category '{category}' is within customer's usual pattern",
            )

        score = 0.5
        return RuleResult(
            rule_type=self.rule_type,
            rule_id=context.rule_parameters.get("rule_id", ""),
            triggered=True,
            risk_score=score,
            severity=RuleResult.score_to_severity(score),
            description=f"Unusual category '{category}' — not in customer's history",
            details={
                "transaction_category": category,
                "usual_categories": usual_categories,
            },
        )
