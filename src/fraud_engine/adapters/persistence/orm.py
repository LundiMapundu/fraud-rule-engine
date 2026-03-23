from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class TransactionModel(Base):
    __tablename__ = "transactions"

    id: Mapped[str] = mapped_column(String(26), primary_key=True)
    customer_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="ZAR")
    merchant: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    channel: Mapped[str] = mapped_column(String(20), nullable=False)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    card_number_hash: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    metadata_: Mapped[dict] = mapped_column("metadata", JSONB, nullable=False, default=dict)
    is_flagged: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )

    __table_args__ = (
        Index("ix_transactions_customer_timestamp", "customer_id", "timestamp"),
        Index("ix_transactions_flagged", "is_flagged"),
    )


class FraudRuleConfigModel(Base):
    __tablename__ = "fraud_rule_configs"

    id: Mapped[str] = mapped_column(String(26), primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    rule_type: Mapped[str] = mapped_column(String(50), nullable=False)
    is_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    parameters: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    risk_weight: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )


class FraudAlertModel(Base):
    __tablename__ = "fraud_alerts"

    id: Mapped[str] = mapped_column(String(26), primary_key=True)
    transaction_id: Mapped[str] = mapped_column(String(26), nullable=False, index=True)
    customer_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    rule_id: Mapped[str] = mapped_column(String(26), nullable=False, index=True)
    rule_type: Mapped[str] = mapped_column(String(50), nullable=False)
    risk_score: Mapped[float] = mapped_column(Float, nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    details: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        Index("ix_fraud_alerts_status", "status"),
        Index("ix_fraud_alerts_severity", "severity"),
    )


class CustomerRiskProfileModel(Base):
    __tablename__ = "customer_risk_profiles"

    id: Mapped[str] = mapped_column(String(26), primary_key=True)
    customer_id: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)
    composite_risk_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    total_alerts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    critical_alerts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    high_alerts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    medium_alerts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    low_alerts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    usual_categories: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    usual_locations: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    avg_transaction_amount: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    total_transactions: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )


class OutboxEventModel(Base):
    __tablename__ = "outbox_events"

    id: Mapped[str] = mapped_column(String(26), primary_key=True)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    is_published: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
