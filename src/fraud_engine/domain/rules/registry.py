from __future__ import annotations

from fraud_engine.domain.enums import RuleType
from fraud_engine.domain.rules.base import FraudRule
from fraud_engine.domain.rules.category_anomaly import CategoryAnomalyRule
from fraud_engine.domain.rules.cumulative import CumulativeAmountRule
from fraud_engine.domain.rules.geographic import GeographicAnomalyRule
from fraud_engine.domain.rules.high_value import HighValueRule
from fraud_engine.domain.rules.time_anomaly import TimeAnomalyRule
from fraud_engine.domain.rules.velocity import VelocityRule

RULE_REGISTRY: dict[RuleType, type[FraudRule]] = {
    RuleType.HIGH_VALUE: HighValueRule,  # type: ignore[type-abstract]
    RuleType.VELOCITY: VelocityRule,  # type: ignore[type-abstract]
    RuleType.GEOGRAPHIC: GeographicAnomalyRule,  # type: ignore[type-abstract]
    RuleType.CATEGORY_ANOMALY: CategoryAnomalyRule,  # type: ignore[type-abstract]
    RuleType.TIME_ANOMALY: TimeAnomalyRule,  # type: ignore[type-abstract]
    RuleType.CUMULATIVE: CumulativeAmountRule,  # type: ignore[type-abstract]
}


def get_rule_instance(rule_type: RuleType) -> FraudRule:
    cls = RULE_REGISTRY.get(rule_type)
    if cls is None:
        raise ValueError(f"Unknown rule type: {rule_type}")
    return cls()  # type: ignore[abstract]
