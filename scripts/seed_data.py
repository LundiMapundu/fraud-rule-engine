"""Seed the database with sample rules and realistic transactions with fraud patterns."""

import asyncio
import hashlib
import random
from datetime import datetime, timedelta

from ulid import ULID
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from fraud_engine.adapters.persistence.orm import (
    Base,
    CustomerRiskProfileModel,
    FraudRuleConfigModel,
    TransactionModel,
)
from fraud_engine.config import settings

CATEGORIES = [
    "groceries", "fuel", "entertainment", "electronics", "travel",
    "restaurants", "healthcare", "utilities", "transfers", "atm", "online_shopping",
]
CHANNELS = ["pos", "online", "atm", "mobile"]
MERCHANTS = [
    "Woolworths", "Pick n Pay", "Checkers", "Shoprite", "Engen", "Shell",
    "Takealot", "Mr Price", "Clicks", "Dis-Chem", "Nando's", "KFC",
    "Uber", "Uber Eats", "Netflix", "Capitec ATM", "FNB ATM",
]

# South African city coordinates
LOCATIONS = [
    (-33.9249, 18.4241, "Cape Town"),
    (-26.2041, 28.0473, "Johannesburg"),
    (-29.8587, 31.0218, "Durban"),
    (-25.7479, 28.2293, "Pretoria"),
    (-33.9608, 25.6022, "Port Elizabeth"),
    (-29.1217, 26.2140, "Bloemfontein"),
]

CUSTOMERS = [f"CUST{str(i).zfill(3)}" for i in range(1, 21)]


def generate_rules() -> list[dict]:
    return [
        {
            "id": str(ULID()),
            "name": "High Value Transaction",
            "rule_type": "high_value",
            "is_enabled": True,
            "parameters": {"threshold_zar": 50000},
            "risk_weight": 1.0,
            "description": "Flag transactions above R50,000",
        },
        {
            "id": str(ULID()),
            "name": "Transaction Velocity",
            "rule_type": "velocity",
            "is_enabled": True,
            "parameters": {"max_count": 5, "window_minutes": 10},
            "risk_weight": 1.2,
            "description": "Flag rapid successive transactions",
        },
        {
            "id": str(ULID()),
            "name": "Geographic Anomaly",
            "rule_type": "geographic",
            "is_enabled": True,
            "parameters": {"max_speed_kmh": 900},
            "risk_weight": 1.5,
            "description": "Flag impossible travel between transactions",
        },
        {
            "id": str(ULID()),
            "name": "Category Anomaly",
            "rule_type": "category_anomaly",
            "is_enabled": True,
            "parameters": {"lookback_days": 90},
            "risk_weight": 0.8,
            "description": "Flag unusual spending categories",
        },
        {
            "id": str(ULID()),
            "name": "Time Anomaly",
            "rule_type": "time_anomaly",
            "is_enabled": True,
            "parameters": {"unusual_hour_start": 1, "unusual_hour_end": 5},
            "risk_weight": 0.6,
            "description": "Flag transactions during unusual hours (01:00-05:00 SAST)",
        },
        {
            "id": str(ULID()),
            "name": "Cumulative Daily Limit",
            "rule_type": "cumulative",
            "is_enabled": True,
            "parameters": {"daily_limit_zar": 100000},
            "risk_weight": 1.0,
            "description": "Flag when daily spending exceeds R100,000",
        },
    ]


def generate_transactions(count: int = 500) -> list[dict]:
    transactions = []
    now = datetime.utcnow()

    for i in range(count):
        customer_id = random.choice(CUSTOMERS)
        loc = random.choice(LOCATIONS)
        is_fraud_pattern = random.random() < 0.1  # 10% fraud-like

        if is_fraud_pattern:
            amount = random.uniform(50000, 500000)
            category = random.choice(["electronics", "travel", "online_shopping"])
            hour_offset = random.randint(0, 3)  # unusual hours UTC
        else:
            amount = random.uniform(20, 15000)
            category = random.choice(CATEGORIES)
            hour_offset = random.randint(6, 22)

        timestamp = now - timedelta(
            days=random.randint(0, 30),
            hours=hour_offset,
            minutes=random.randint(0, 59),
        )

        card_hash = hashlib.sha256(f"{customer_id}-card".encode()).hexdigest()[:16]

        transactions.append({
            "id": str(ULID()),
            "customer_id": customer_id,
            "amount": round(amount, 2),
            "currency": "ZAR",
            "merchant": random.choice(MERCHANTS),
            "category": category,
            "channel": random.choice(CHANNELS),
            "latitude": loc[0] + random.uniform(-0.1, 0.1),
            "longitude": loc[1] + random.uniform(-0.1, 0.1),
            "timestamp": timestamp,
            "card_number_hash": card_hash,
            "metadata_": {},
            "is_flagged": False,
        })

    return transactions


def generate_profiles() -> list[dict]:
    profiles = []
    for cid in CUSTOMERS:
        profiles.append({
            "id": str(ULID()),
            "customer_id": cid,
            "composite_risk_score": round(random.uniform(0, 0.3), 3),
            "total_alerts": 0,
            "critical_alerts": 0,
            "high_alerts": 0,
            "medium_alerts": 0,
            "low_alerts": 0,
            "usual_categories": random.sample(CATEGORIES, k=random.randint(3, 6)),
            "usual_locations": [],
            "avg_transaction_amount": round(random.uniform(500, 5000), 2),
            "total_transactions": random.randint(50, 500),
        })
    return profiles


async def seed() -> None:
    engine = create_async_engine(settings.database_url)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        # Rules
        for rule_data in generate_rules():
            session.add(FraudRuleConfigModel(**rule_data))

        # Transactions
        for txn_data in generate_transactions(500):
            session.add(TransactionModel(**txn_data))

        # Profiles
        for profile_data in generate_profiles():
            session.add(CustomerRiskProfileModel(**profile_data))

        await session.commit()

    await engine.dispose()
    print(f"Seeded: 6 rules, 500 transactions, {len(CUSTOMERS)} customer profiles")


if __name__ == "__main__":
    asyncio.run(seed())
