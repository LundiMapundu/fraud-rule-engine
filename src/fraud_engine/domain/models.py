from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from fraud_engine.domain.enums import (
    AlertStatus,
    RiskLevel,
    RuleType,
    TransactionCategory,
    TransactionChannel,
)


@dataclass
class Transaction:
    id: str
    customer_id: str
    amount: float
    currency: str
    merchant: str
    category: TransactionCategory
    channel: TransactionChannel
    latitude: float | None
    longitude: float | None
    timestamp: datetime
    card_number_hash: str
    metadata: dict[str, Any] = field(default_factory=dict)
    is_flagged: bool = False
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class FraudRuleConfig:
    id: str
    name: str
    rule_type: RuleType
    is_enabled: bool
    parameters: dict[str, Any]
    risk_weight: float
    description: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class FraudAlert:
    id: str
    transaction_id: str
    customer_id: str
    rule_id: str
    rule_type: RuleType
    risk_score: float
    severity: RiskLevel
    description: str
    details: dict[str, Any] = field(default_factory=dict)
    status: AlertStatus = AlertStatus.PENDING
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class CustomerRiskProfile:
    id: str
    customer_id: str
    composite_risk_score: float = 0.0
    total_alerts: int = 0
    critical_alerts: int = 0
    high_alerts: int = 0
    medium_alerts: int = 0
    low_alerts: int = 0
    usual_categories: list[str] = field(default_factory=list)
    usual_locations: list[dict[str, float]] = field(default_factory=list)
    avg_transaction_amount: float = 0.0
    total_transactions: int = 0
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class OutboxEvent:
    id: str
    event_type: str
    payload: dict[str, Any]
    is_published: bool = False
    created_at: datetime = field(default_factory=datetime.utcnow)
