from datetime import datetime, timedelta

from fraud_engine.domain.rules.cumulative import CumulativeAmountRule
from tests.unit.domain.rules.conftest import make_context, make_transaction


class TestCumulativeAmountRule:
    def setup_method(self):
        self.rule = CumulativeAmountRule()

    def test_within_limit_not_triggered(self):
        now = datetime(2026, 3, 22, 12, 0, 0)
        txn = make_transaction(id="TXN005", amount=20_000, timestamp=now)
        recent = [
            make_transaction(id=f"TXN00{i}", amount=10_000, timestamp=now - timedelta(hours=i))
            for i in range(1, 4)
        ]
        ctx = make_context(
            transaction=txn,
            recent_transactions=recent,
            rule_parameters={"daily_limit_zar": 100_000},
        )
        result = self.rule.evaluate(ctx)
        assert not result.triggered

    def test_exceeds_limit_triggered(self):
        now = datetime(2026, 3, 22, 12, 0, 0)
        txn = make_transaction(id="TXN005", amount=50_000, timestamp=now)
        recent = [
            make_transaction(id=f"TXN00{i}", amount=30_000, timestamp=now - timedelta(hours=i))
            for i in range(1, 4)
        ]
        ctx = make_context(
            transaction=txn,
            recent_transactions=recent,
            rule_parameters={"daily_limit_zar": 100_000},
        )
        result = self.rule.evaluate(ctx)
        assert result.triggered
        assert "exceeds limit" in result.description

    def test_transactions_from_different_day_excluded(self):
        now = datetime(2026, 3, 22, 12, 0, 0)
        txn = make_transaction(id="TXN005", amount=50_000, timestamp=now)
        recent = [
            make_transaction(id=f"TXN00{i}", amount=50_000, timestamp=now - timedelta(days=1))
            for i in range(1, 4)
        ]
        ctx = make_context(
            transaction=txn,
            recent_transactions=recent,
            rule_parameters={"daily_limit_zar": 100_000},
        )
        result = self.rule.evaluate(ctx)
        assert not result.triggered
