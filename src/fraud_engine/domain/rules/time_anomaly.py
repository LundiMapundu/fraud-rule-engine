from __future__ import annotations

from fraud_engine.domain.enums import RuleType
from fraud_engine.domain.rules.base import EvaluationContext, RuleResult

# South African Standard Time offset (UTC+2)
SAST_OFFSET_HOURS = 2


class TimeAnomalyRule:
    """Flags transactions occurring at unusual hours (e.g. 01:00-05:00 SAST)."""

    rule_type = RuleType.TIME_ANOMALY

    def evaluate(self, context: EvaluationContext) -> RuleResult:
        unusual_start = context.rule_parameters.get("unusual_hour_start", 1)
        unusual_end = context.rule_parameters.get("unusual_hour_end", 5)

        txn = context.transaction
        # Convert UTC timestamp to SAST
        hour_sast = (txn.timestamp.hour + SAST_OFFSET_HOURS) % 24

        if not (unusual_start <= hour_sast < unusual_end):
            return RuleResult(
                rule_type=self.rule_type,
                rule_id=context.rule_parameters.get("rule_id", ""),
                triggered=False,
                risk_score=0.0,
                severity=RuleResult.score_to_severity(0.0),
                description=f"Transaction at {hour_sast:02d}:00 SAST is within normal hours",
            )

        score = 0.4
        return RuleResult(
            rule_type=self.rule_type,
            rule_id=context.rule_parameters.get("rule_id", ""),
            triggered=True,
            risk_score=score,
            severity=RuleResult.score_to_severity(score),
            description=(
                f"Transaction at {hour_sast:02d}:00 SAST is during unusual hours "
                f"({unusual_start:02d}:00-{unusual_end:02d}:00)"
            ),
            details={
                "hour_sast": hour_sast,
                "unusual_range": f"{unusual_start:02d}:00-{unusual_end:02d}:00",
            },
        )
