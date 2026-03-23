from datetime import datetime

from fraud_engine.domain.engine import RuleEngine
from fraud_engine.domain.enums import RiskLevel, RuleType, TransactionCategory, TransactionChannel
from fraud_engine.domain.models import FraudRuleConfig, Transaction
from fraud_engine.domain.rules.base import RuleResult


class TestRuleEngine:
    def setup_method(self):
        self.engine = RuleEngine()

    def _make_txn(self, **overrides) -> Transaction:
        defaults = {
            "id": "TXN001",
            "customer_id": "CUST001",
            "amount": 1000.0,
            "currency": "ZAR",
            "merchant": "Test",
            "category": TransactionCategory.GROCERIES,
            "channel": TransactionChannel.POS,
            "latitude": None,
            "longitude": None,
            "timestamp": datetime(2026, 3, 22, 12, 0, 0),
            "card_number_hash": "abc",
        }
        defaults.update(overrides)
        return Transaction(**defaults)

    def test_no_rules_returns_empty(self):
        txn = self._make_txn()
        results = self.engine.evaluate(txn, [], None, [])
        assert results == []

    def test_disabled_rules_skipped(self):
        txn = self._make_txn(amount=100_000)
        rules = [
            FraudRuleConfig(
                id="R1",
                name="High Value",
                rule_type=RuleType.HIGH_VALUE,
                is_enabled=False,
                parameters={"threshold_zar": 50_000},
                risk_weight=1.0,
            )
        ]
        results = self.engine.evaluate(txn, rules, None, [])
        assert len(results) == 0

    def test_enabled_rule_evaluates(self):
        txn = self._make_txn(amount=100_000)
        rules = [
            FraudRuleConfig(
                id="R1",
                name="High Value",
                rule_type=RuleType.HIGH_VALUE,
                is_enabled=True,
                parameters={"threshold_zar": 50_000},
                risk_weight=1.0,
            )
        ]
        results = self.engine.evaluate(txn, rules, None, [])
        assert len(results) == 1
        assert results[0].triggered

    def test_composite_score_no_triggers(self):
        score = RuleEngine.compute_composite_score([])
        assert score == 0.0

    def test_composite_score_single_trigger(self):
        results = [
            RuleResult(
                rule_type=RuleType.HIGH_VALUE,
                rule_id="R1",
                triggered=True,
                risk_score=0.7,
                severity=RiskLevel.HIGH,
                description="test",
            )
        ]
        score = RuleEngine.compute_composite_score(results)
        assert score == 0.7

    def test_composite_score_multiple_triggers(self):
        results = [
            RuleResult(
                rule_type=RuleType.HIGH_VALUE,
                rule_id="R1",
                triggered=True,
                risk_score=0.6,
                severity=RiskLevel.HIGH,
                description="test",
            ),
            RuleResult(
                rule_type=RuleType.VELOCITY,
                rule_id="R2",
                triggered=True,
                risk_score=0.8,
                severity=RiskLevel.CRITICAL,
                description="test",
            ),
        ]
        score = RuleEngine.compute_composite_score(results)
        # (0.6 + 0.8) / 2 + 0.1 * (2 - 1) = 0.7 + 0.1 = 0.8
        assert abs(score - 0.8) < 1e-10
