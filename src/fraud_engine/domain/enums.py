from __future__ import annotations

from enum import StrEnum


class TransactionCategory(StrEnum):
    GROCERIES = "groceries"
    FUEL = "fuel"
    ENTERTAINMENT = "entertainment"
    ELECTRONICS = "electronics"
    TRAVEL = "travel"
    RESTAURANTS = "restaurants"
    HEALTHCARE = "healthcare"
    UTILITIES = "utilities"
    TRANSFERS = "transfers"
    ATM = "atm"
    ONLINE_SHOPPING = "online_shopping"
    OTHER = "other"


class TransactionChannel(StrEnum):
    POS = "pos"
    ONLINE = "online"
    ATM = "atm"
    MOBILE = "mobile"
    BRANCH = "branch"


class RuleType(StrEnum):
    HIGH_VALUE = "high_value"
    VELOCITY = "velocity"
    GEOGRAPHIC = "geographic"
    CATEGORY_ANOMALY = "category_anomaly"
    TIME_ANOMALY = "time_anomaly"
    CUMULATIVE = "cumulative"


class RiskLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertStatus(StrEnum):
    PENDING = "pending"
    INVESTIGATING = "investigating"
    CONFIRMED = "confirmed"
    RESOLVED = "resolved"
    FALSE_POSITIVE = "false_positive"
