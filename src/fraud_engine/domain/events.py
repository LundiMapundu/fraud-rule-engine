from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class DomainEvent:
    event_id: str
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass(frozen=True)
class TransactionReceived(DomainEvent):
    transaction_id: str = ""
    customer_id: str = ""
    amount: float = 0.0
    payload: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class FraudDetected(DomainEvent):
    transaction_id: str = ""
    customer_id: str = ""
    alert_ids: list[str] = field(default_factory=list)
    composite_risk_score: float = 0.0
    severity: str = ""
