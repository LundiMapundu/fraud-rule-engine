from __future__ import annotations

from fraud_engine.domain.enums import RuleType
from fraud_engine.domain.rules.base import EvaluationContext, RuleResult


class HighValueRule:
    """Flags transactions exceeding a configurable ZAR threshold."""

    rule_type = RuleType.HIGH_VALUE

    def evaluate(self, context: EvaluationContext) -> RuleResult:
        threshold = context.rule_parameters.get("threshold_zar", 50_000)
        amount = context.transaction.amount

        if amount <= threshold:
            return RuleResult(
                rule_type=self.rule_type,
                rule_id=context.rule_parameters.get("rule_id", ""),
                triggered=False,
                risk_score=0.0,
                severity=RuleResult.score_to_severity(0.0),
                description="Transaction amount within normal range",
            )

        # Score scales with how far over the threshold
        ratio = amount / threshold
        score = min(1.0, 0.4 + (ratio - 1.0) * 0.3)

        return RuleResult(
            rule_type=self.rule_type,
            rule_id=context.rule_parameters.get("rule_id", ""),
            triggered=True,
            risk_score=score,
            severity=RuleResult.score_to_severity(score),
            description=(
                f"High-value transaction: R{amount:,.2f} exceeds threshold R{threshold:,.2f}"
            ),
            details={"amount": amount, "threshold": threshold, "ratio": round(ratio, 2)},
        )
