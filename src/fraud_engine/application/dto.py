from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from fraud_engine.domain.enums import (
    AlertStatus,
    RuleType,
    TransactionCategory,
    TransactionChannel,
)


@dataclass
class CreateTransactionDTO:
    customer_id: str
    amount: float
    currency: str
    merchant: str
    category: TransactionCategory
    channel: TransactionChannel
    latitude: float | None = None
    longitude: float | None = None
    timestamp: datetime | None = None
    card_number_hash: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class CreateRuleDTO:
    name: str
    rule_type: RuleType
    parameters: dict[str, Any]
    risk_weight: float = 1.0
    is_enabled: bool = True
    description: str = ""


@dataclass
class UpdateRuleDTO:
    name: str | None = None
    parameters: dict[str, Any] | None = None
    risk_weight: float | None = None
    is_enabled: bool | None = None
    description: str | None = None


@dataclass
class TransactionResultDTO:
    transaction_id: str
    is_flagged: bool
    alerts: list[dict[str, Any]] = field(default_factory=list)
    composite_risk_score: float = 0.0
    severity: str = ""


@dataclass
class UpdateAlertDTO:
    status: AlertStatus


@dataclass
class AnalyticsOverviewDTO:
    total_transactions: int
    total_alerts: int
    alerts_by_severity: dict[str, int]
    alerts_by_status: dict[str, int]
    avg_risk_score: float
    flagged_transaction_rate: float


@dataclass
class RuleEffectivenessDTO:
    rule_id: str
    rule_name: str
    rule_type: RuleType
    total_alerts: int
    confirmed_alerts: int
    false_positive_rate: float
    avg_risk_score: float
