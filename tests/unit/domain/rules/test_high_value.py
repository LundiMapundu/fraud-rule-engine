from fraud_engine.domain.rules.high_value import HighValueRule
from tests.unit.domain.rules.conftest import make_context, make_transaction


class TestHighValueRule:
    def setup_method(self):
        self.rule = HighValueRule()

    def test_below_threshold_not_triggered(self):
        txn = make_transaction(amount=10_000)
        ctx = make_context(transaction=txn, rule_parameters={"threshold_zar": 50_000})
        result = self.rule.evaluate(ctx)
        assert not result.triggered
        assert result.risk_score == 0.0

    def test_above_threshold_triggered(self):
        txn = make_transaction(amount=75_000)
        ctx = make_context(transaction=txn, rule_parameters={"threshold_zar": 50_000})
        result = self.rule.evaluate(ctx)
        assert result.triggered
        assert result.risk_score > 0.0
        assert "75,000" in result.description

    def test_exactly_at_threshold_not_triggered(self):
        txn = make_transaction(amount=50_000)
        ctx = make_context(transaction=txn, rule_parameters={"threshold_zar": 50_000})
        result = self.rule.evaluate(ctx)
        assert not result.triggered

    def test_very_high_amount_high_score(self):
        txn = make_transaction(amount=500_000)
        ctx = make_context(transaction=txn, rule_parameters={"threshold_zar": 50_000})
        result = self.rule.evaluate(ctx)
        assert result.triggered
        assert result.risk_score == 1.0

    def test_default_threshold(self):
        txn = make_transaction(amount=60_000)
        ctx = make_context(transaction=txn, rule_parameters={})
        result = self.rule.evaluate(ctx)
        assert result.triggered
