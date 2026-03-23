"""Initial schema

Revision ID: 001
Revises:
Create Date: 2026-03-22
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Transactions
    op.create_table(
        "transactions",
        sa.Column("id", sa.String(26), primary_key=True),
        sa.Column("customer_id", sa.String(50), nullable=False),
        sa.Column("amount", sa.Float, nullable=False),
        sa.Column("currency", sa.String(3), nullable=False, server_default="ZAR"),
        sa.Column("merchant", sa.String(255), nullable=False),
        sa.Column("category", sa.String(50), nullable=False),
        sa.Column("channel", sa.String(20), nullable=False),
        sa.Column("latitude", sa.Float, nullable=True),
        sa.Column("longitude", sa.Float, nullable=True),
        sa.Column("timestamp", sa.DateTime, nullable=False),
        sa.Column("card_number_hash", sa.String(64), nullable=False, server_default=""),
        sa.Column("metadata", JSONB, nullable=False, server_default="{}"),
        sa.Column("is_flagged", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_transactions_customer_id", "transactions", ["customer_id"])
    op.create_index(
        "ix_transactions_customer_timestamp", "transactions", ["customer_id", "timestamp"]
    )
    op.create_index("ix_transactions_flagged", "transactions", ["is_flagged"])

    # Fraud rule configs
    op.create_table(
        "fraud_rule_configs",
        sa.Column("id", sa.String(26), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False, unique=True),
        sa.Column("rule_type", sa.String(50), nullable=False),
        sa.Column("is_enabled", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("parameters", JSONB, nullable=False, server_default="{}"),
        sa.Column("risk_weight", sa.Float, nullable=False, server_default="1.0"),
        sa.Column("description", sa.Text, nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )

    # Fraud alerts
    op.create_table(
        "fraud_alerts",
        sa.Column("id", sa.String(26), primary_key=True),
        sa.Column("transaction_id", sa.String(26), nullable=False),
        sa.Column("customer_id", sa.String(50), nullable=False),
        sa.Column("rule_id", sa.String(26), nullable=False),
        sa.Column("rule_type", sa.String(50), nullable=False),
        sa.Column("risk_score", sa.Float, nullable=False),
        sa.Column("severity", sa.String(20), nullable=False),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("details", JSONB, nullable=False, server_default="{}"),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_fraud_alerts_transaction_id", "fraud_alerts", ["transaction_id"])
    op.create_index("ix_fraud_alerts_customer_id", "fraud_alerts", ["customer_id"])
    op.create_index("ix_fraud_alerts_rule_id", "fraud_alerts", ["rule_id"])
    op.create_index("ix_fraud_alerts_status", "fraud_alerts", ["status"])
    op.create_index("ix_fraud_alerts_severity", "fraud_alerts", ["severity"])

    # Customer risk profiles
    op.create_table(
        "customer_risk_profiles",
        sa.Column("id", sa.String(26), primary_key=True),
        sa.Column("customer_id", sa.String(50), nullable=False, unique=True),
        sa.Column("composite_risk_score", sa.Float, nullable=False, server_default="0.0"),
        sa.Column("total_alerts", sa.Integer, nullable=False, server_default="0"),
        sa.Column("critical_alerts", sa.Integer, nullable=False, server_default="0"),
        sa.Column("high_alerts", sa.Integer, nullable=False, server_default="0"),
        sa.Column("medium_alerts", sa.Integer, nullable=False, server_default="0"),
        sa.Column("low_alerts", sa.Integer, nullable=False, server_default="0"),
        sa.Column("usual_categories", JSONB, nullable=False, server_default="[]"),
        sa.Column("usual_locations", JSONB, nullable=False, server_default="[]"),
        sa.Column("avg_transaction_amount", sa.Float, nullable=False, server_default="0.0"),
        sa.Column("total_transactions", sa.Integer, nullable=False, server_default="0"),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )
    op.create_index(
        "ix_customer_risk_profiles_customer_id", "customer_risk_profiles", ["customer_id"]
    )

    # Outbox events
    op.create_table(
        "outbox_events",
        sa.Column("id", sa.String(26), primary_key=True),
        sa.Column("event_type", sa.String(100), nullable=False),
        sa.Column("payload", JSONB, nullable=False),
        sa.Column("is_published", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_outbox_events_is_published", "outbox_events", ["is_published"])


def downgrade() -> None:
    op.drop_table("outbox_events")
    op.drop_table("customer_risk_profiles")
    op.drop_table("fraud_alerts")
    op.drop_table("fraud_rule_configs")
    op.drop_table("transactions")
