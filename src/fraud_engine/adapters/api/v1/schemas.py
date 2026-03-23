from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from fraud_engine.domain.enums import (
    AlertStatus,
    RuleType,
    TransactionCategory,
    TransactionChannel,
)


# --- Transactions ---
class CreateTransactionRequest(BaseModel):
    customer_id: str = Field(..., min_length=1, max_length=50, examples=["CUST001"])
    amount: float = Field(..., gt=0, examples=[15000.00])
    currency: str = Field(default="ZAR", max_length=3, examples=["ZAR"])
    merchant: str = Field(..., min_length=1, max_length=255, examples=["Woolworths"])
    category: TransactionCategory = Field(examples=[TransactionCategory.GROCERIES])
    channel: TransactionChannel = Field(examples=[TransactionChannel.POS])
    latitude: float | None = Field(default=None, ge=-90, le=90, examples=[-33.9249])
    longitude: float | None = Field(default=None, ge=-180, le=180, examples=[18.4241])
    timestamp: datetime | None = Field(default=None)
    card_number_hash: str = Field(default="", max_length=64)
    metadata: dict[str, Any] = Field(default_factory=dict)


class TransactionResponse(BaseModel):
    id: str
    customer_id: str
    amount: float
    currency: str
    merchant: str
    category: str
    channel: str
    latitude: float | None
    longitude: float | None
    timestamp: datetime
    is_flagged: bool
    created_at: datetime


class TransactionResultResponse(BaseModel):
    transaction_id: str
    is_flagged: bool
    alerts: list[dict[str, Any]]
    composite_risk_score: float
    severity: str


class TransactionDetailResponse(TransactionResponse):
    alerts: list[dict[str, Any]] = Field(default_factory=list)


# --- Rules ---
class CreateRuleRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, examples=["High Value Check"])
    rule_type: RuleType = Field(examples=[RuleType.HIGH_VALUE])
    parameters: dict[str, Any] = Field(examples=[{"threshold_zar": 50000}])
    risk_weight: float = Field(default=1.0, ge=0.0, le=5.0)
    is_enabled: bool = Field(default=True)
    description: str = Field(default="")


class UpdateRuleRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    parameters: dict[str, Any] | None = None
    risk_weight: float | None = Field(default=None, ge=0.0, le=5.0)
    is_enabled: bool | None = None
    description: str | None = None


class RuleResponse(BaseModel):
    id: str
    name: str
    rule_type: str
    is_enabled: bool
    parameters: dict[str, Any]
    risk_weight: float
    description: str
    created_at: datetime
    updated_at: datetime


# --- Alerts ---
class UpdateAlertRequest(BaseModel):
    status: AlertStatus


class AlertResponse(BaseModel):
    id: str
    transaction_id: str
    customer_id: str
    rule_id: str
    rule_type: str
    risk_score: float
    severity: str
    description: str
    details: dict[str, Any]
    status: str
    created_at: datetime
    updated_at: datetime


class AlertSummaryResponse(BaseModel):
    total_alerts: int
    alerts_by_severity: dict[str, int]
    alerts_by_status: dict[str, int]
    avg_risk_score: float


# --- Analytics ---
class AnalyticsOverviewResponse(BaseModel):
    total_alerts: int
    alerts_by_severity: dict[str, int]
    alerts_by_status: dict[str, int]
    avg_risk_score: float


# --- Customers ---
class CustomerProfileResponse(BaseModel):
    id: str
    customer_id: str
    composite_risk_score: float
    total_alerts: int
    critical_alerts: int
    high_alerts: int
    medium_alerts: int
    low_alerts: int
    usual_categories: list[str]
    avg_transaction_amount: float
    total_transactions: int


# --- Pagination ---
class PaginatedResponse(BaseModel):
    items: list[Any]
    total: int
    page: int
    page_size: int
    pages: int
