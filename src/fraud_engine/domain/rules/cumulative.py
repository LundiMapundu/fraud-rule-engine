from __future__ import annotations

from datetime import timedelta

from fraud_engine.domain.enums import RuleType
from fraud_engine.domain.rules.base import EvaluationContext, RuleResult


class CumulativeAmountRule:
    """Flags when daily spending for a customer exceeds a limit."""

    rule_type = RuleType.CUMULATIVE

    def evaluate(self, context: EvaluationContext) -> RuleResult:
        daily_limit = context.rule_parameters.get("daily_limit_zar", 100_000)

        txn = context.transaction
        day_start = txn.timestamp.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)

        daily_total = txn.amount
        for t in context.recent_transactions:
            if (
                t.customer_id == txn.customer_id
                and t.id != txn.id
                and day_start <= t.timestamp < day_end
            ):
                daily_total += t.amount

        if daily_total <= daily_limit:
            return RuleResult(
                rule_type=self.rule_type,
                rule_id=context.rule_parameters.get("rule_id", ""),
                triggered=False,
                risk_score=0.0,
                severity=RuleResult.score_to_severity(0.0),
                description=(
                    f"Daily spending R{daily_total:,.2f} within limit R{daily_limit:,.2f}"
                ),
            )

        ratio = daily_total / daily_limit
        score = min(1.0, 0.5 + (ratio - 1.0) * 0.25)

        return RuleResult(
            rule_type=self.rule_type,
            rule_id=context.rule_parameters.get("rule_id", ""),
            triggered=True,
            risk_score=score,
            severity=RuleResult.score_to_severity(score),
            description=(f"Daily spending R{daily_total:,.2f} exceeds limit R{daily_limit:,.2f}"),
            details={
                "daily_total": daily_total,
                "daily_limit": daily_limit,
                "ratio": round(ratio, 2),
            },
        )
