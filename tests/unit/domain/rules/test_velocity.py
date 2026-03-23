from datetime import datetime, timedelta

from fraud_engine.domain.rules.velocity import VelocityRule
from tests.unit.domain.rules.conftest import make_context, make_transaction


class TestVelocityRule:
    def setup_method(self):
        self.rule = VelocityRule()

    def test_normal_velocity_not_triggered(self):
        now = datetime(2026, 3, 22, 12, 0, 0)
        txn = make_transaction(id="TXN006", timestamp=now)
        recent = [
            make_transaction(id=f"TXN00{i}", timestamp=now - timedelta(minutes=i))
            for i in range(1, 4)
        ]
        ctx = make_context(
            transaction=txn,
            recent_transactions=recent,
            rule_parameters={"max_count": 5, "window_minutes": 10},
        )
        result = self.rule.evaluate(ctx)
        assert not result.triggered

    def test_high_velocity_triggered(self):
        now = datetime(2026, 3, 22, 12, 0, 0)
        txn = make_transaction(id="TXN010", timestamp=now)
        recent = [
            make_transaction(id=f"TXN00{i}", timestamp=now - timedelta(minutes=i))
            for i in range(1, 8)
        ]
        ctx = make_context(
            transaction=txn,
            recent_transactions=recent,
            rule_parameters={"max_count": 5, "window_minutes": 10},
        )
        result = self.rule.evaluate(ctx)
        assert result.triggered
        assert "Velocity breach" in result.description

    def test_transactions_outside_window_ignored(self):
        now = datetime(2026, 3, 22, 12, 0, 0)
        txn = make_transaction(id="TXN010", timestamp=now)
        recent = [
            make_transaction(id=f"TXN00{i}", timestamp=now - timedelta(hours=1))
            for i in range(1, 8)
        ]
        ctx = make_context(
            transaction=txn,
            recent_transactions=recent,
            rule_parameters={"max_count": 5, "window_minutes": 10},
        )
        result = self.rule.evaluate(ctx)
        assert not result.triggered
