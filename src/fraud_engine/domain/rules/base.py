from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol

from fraud_engine.domain.enums import RiskLevel, RuleType
from fraud_engine.domain.models import CustomerRiskProfile, Transaction


@dataclass
class EvaluationContext:
    """Context provided to each rule during evaluation."""

    transaction: Transaction
    customer_profile: CustomerRiskProfile | None
    recent_transactions: list[Transaction]
    rule_parameters: dict[str, Any]


@dataclass
class RuleResult:
    """Result of a single rule evaluation."""

    rule_type: RuleType
    rule_id: str
    triggered: bool
    risk_score: float  # 0.0 - 1.0
    severity: RiskLevel
    description: str
    details: dict[str, Any] = field(default_factory=dict)

    @staticmethod
    def score_to_severity(score: float) -> RiskLevel:
        if score >= 0.8:
            return RiskLevel.CRITICAL
        if score >= 0.6:
            return RiskLevel.HIGH
        if score >= 0.4:
            return RiskLevel.MEDIUM
        return RiskLevel.LOW


class FraudRule(Protocol):
    """Protocol that all fraud detection rules must implement."""

    rule_type: RuleType

    def evaluate(self, context: EvaluationContext) -> RuleResult: ...
