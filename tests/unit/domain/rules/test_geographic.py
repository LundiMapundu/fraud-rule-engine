from datetime import datetime, timedelta

from fraud_engine.domain.rules.geographic import GeographicAnomalyRule, haversine_km
from tests.unit.domain.rules.conftest import make_context, make_transaction


class TestGeographicAnomalyRule:
    def setup_method(self):
        self.rule = GeographicAnomalyRule()

    def test_haversine_known_distance(self):
        # Cape Town to Johannesburg ~1260 km
        dist = haversine_km(-33.9249, 18.4241, -26.2041, 28.0473)
        assert 1200 < dist < 1350

    def test_no_location_not_triggered(self):
        txn = make_transaction(latitude=None, longitude=None)
        ctx = make_context(transaction=txn, rule_parameters={"max_speed_kmh": 900})
        result = self.rule.evaluate(ctx)
        assert not result.triggered

    def test_impossible_travel_triggered(self):
        now = datetime(2026, 3, 22, 12, 0, 0)
        # Cape Town transaction 30 minutes ago
        prior = make_transaction(
            id="TXN001",
            latitude=-33.9249,
            longitude=18.4241,
            timestamp=now - timedelta(minutes=30),
        )
        # Johannesburg transaction now (~1260 km in 30 min = ~2520 km/h)
        txn = make_transaction(
            id="TXN002",
            latitude=-26.2041,
            longitude=28.0473,
            timestamp=now,
        )
        ctx = make_context(
            transaction=txn,
            recent_transactions=[prior],
            rule_parameters={"max_speed_kmh": 900},
        )
        result = self.rule.evaluate(ctx)
        assert result.triggered
        assert "Impossible travel" in result.description

    def test_plausible_travel_not_triggered(self):
        now = datetime(2026, 3, 22, 12, 0, 0)
        prior = make_transaction(
            id="TXN001",
            latitude=-33.9249,
            longitude=18.4241,
            timestamp=now - timedelta(hours=3),
        )
        txn = make_transaction(
            id="TXN002",
            latitude=-26.2041,
            longitude=28.0473,
            timestamp=now,
        )
        ctx = make_context(
            transaction=txn,
            recent_transactions=[prior],
            rule_parameters={"max_speed_kmh": 900},
        )
        result = self.rule.evaluate(ctx)
        assert not result.triggered
