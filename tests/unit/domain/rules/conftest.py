from datetime import datetime

from fraud_engine.domain.enums import TransactionCategory, TransactionChannel
from fraud_engine.domain.models import CustomerRiskProfile, Transaction
from fraud_engine.domain.rules.base import EvaluationContext


def make_transaction(**overrides) -> Transaction:
    defaults = {
        "id": "TXN001",
        "customer_id": "CUST001",
        "amount": 1000.0,
        "currency": "ZAR",
        "merchant": "Test Shop",
        "category": TransactionCategory.GROCERIES,
        "channel": TransactionChannel.POS,
        "latitude": -33.9249,
        "longitude": 18.4241,
        "timestamp": datetime(2026, 3, 22, 12, 0, 0),
        "card_number_hash": "abc123",
    }
    defaults.update(overrides)
    return Transaction(**defaults)


def make_context(
    transaction: Transaction | None = None,
    customer_profile: CustomerRiskProfile | None = None,
    recent_transactions: list[Transaction] | None = None,
    rule_parameters: dict | None = None,
) -> EvaluationContext:
    return EvaluationContext(
        transaction=transaction or make_transaction(),
        customer_profile=customer_profile,
        recent_transactions=recent_transactions or [],
        rule_parameters=rule_parameters or {},
    )
