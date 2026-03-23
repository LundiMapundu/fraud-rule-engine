from datetime import datetime

from fraud_engine.domain.rules.time_anomaly import TimeAnomalyRule
from tests.unit.domain.rules.conftest import make_context, make_transaction


class TestTimeAnomalyRule:
    def setup_method(self):
        self.rule = TimeAnomalyRule()

    def test_normal_hours_not_triggered(self):
        # 10:00 UTC = 12:00 SAST
        txn = make_transaction(timestamp=datetime(2026, 3, 22, 10, 0, 0))
        ctx = make_context(
            transaction=txn,
            rule_parameters={"unusual_hour_start": 1, "unusual_hour_end": 5},
        )
        result = self.rule.evaluate(ctx)
        assert not result.triggered

    def test_unusual_hours_triggered(self):
        # 01:00 UTC = 03:00 SAST (within 01:00-05:00 SAST)
        txn = make_transaction(timestamp=datetime(2026, 3, 22, 1, 0, 0))
        ctx = make_context(
            transaction=txn,
            rule_parameters={"unusual_hour_start": 1, "unusual_hour_end": 5},
        )
        result = self.rule.evaluate(ctx)
        assert result.triggered
        assert "unusual hours" in result.description.lower()

    def test_edge_of_window(self):
        # 23:00 UTC = 01:00 SAST (start of unusual window)
        txn = make_transaction(timestamp=datetime(2026, 3, 22, 23, 0, 0))
        ctx = make_context(
            transaction=txn,
            rule_parameters={"unusual_hour_start": 1, "unusual_hour_end": 5},
        )
        result = self.rule.evaluate(ctx)
        assert result.triggered
