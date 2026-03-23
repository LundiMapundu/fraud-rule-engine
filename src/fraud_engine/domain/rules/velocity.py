from __future__ import annotations

from datetime import timedelta

from fraud_engine.domain.enums import RuleType
from fraud_engine.domain.rules.base import EvaluationContext, RuleResult


class VelocityRule:
    """Flags when a customer makes too many transactions in a short window."""

    rule_type = RuleType.VELOCITY

    def evaluate(self, context: EvaluationContext) -> RuleResult:
        max_count = context.rule_parameters.get("max_count", 5)
        window_minutes = context.rule_parameters.get("window_minutes", 10)

        txn = context.transaction
        window_start = txn.timestamp - timedelta(minutes=window_minutes)

        recent_in_window = [
            t
            for t in context.recent_transactions
            if t.customer_id == txn.customer_id and t.timestamp >= window_start and t.id != txn.id
        ]

        count = len(recent_in_window) + 1  # include current

        if count <= max_count:
            return RuleResult(
                rule_type=self.rule_type,
                rule_id=context.rule_parameters.get("rule_id", ""),
                triggered=False,
                risk_score=0.0,
                severity=RuleResult.score_to_severity(0.0),
                description=(
                    f"Transaction velocity normal: {count}/{max_count} in {window_minutes}min"
                ),
            )

        ratio = count / max_count
        score = min(1.0, 0.5 + (ratio - 1.0) * 0.25)

        return RuleResult(
            rule_type=self.rule_type,
            rule_id=context.rule_parameters.get("rule_id", ""),
            triggered=True,
            risk_score=score,
            severity=RuleResult.score_to_severity(score),
            description=(
                f"Velocity breach: {count} transactions in {window_minutes}min (limit: {max_count})"
            ),
            details={
                "count": count,
                "max_count": max_count,
                "window_minutes": window_minutes,
            },
        )
