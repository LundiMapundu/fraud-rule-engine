from __future__ import annotations

import math
from datetime import timedelta

from fraud_engine.domain.enums import RuleType
from fraud_engine.domain.rules.base import EvaluationContext, RuleResult


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the great-circle distance between two points on Earth in km."""
    earth_radius = 6371.0
    lat1_r, lat2_r = math.radians(lat1), math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1_r) * math.cos(lat2_r) * math.sin(dlon / 2) ** 2
    return earth_radius * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


class GeographicAnomalyRule:
    """Detects impossible travel — large distance in short time between transactions."""

    rule_type = RuleType.GEOGRAPHIC

    def evaluate(self, context: EvaluationContext) -> RuleResult:
        max_speed_kmh = context.rule_parameters.get("max_speed_kmh", 900)
        txn = context.transaction

        if txn.latitude is None or txn.longitude is None:
            return RuleResult(
                rule_type=self.rule_type,
                rule_id=context.rule_parameters.get("rule_id", ""),
                triggered=False,
                risk_score=0.0,
                severity=RuleResult.score_to_severity(0.0),
                description="No location data available for geographic check",
            )

        # Find the most recent prior transaction with location data
        prior = None
        for t in sorted(context.recent_transactions, key=lambda x: x.timestamp, reverse=True):
            if (
                t.customer_id == txn.customer_id
                and t.id != txn.id
                and t.latitude is not None
                and t.longitude is not None
                and t.timestamp < txn.timestamp
            ):
                prior = t
                break

        if prior is None:
            return RuleResult(
                rule_type=self.rule_type,
                rule_id=context.rule_parameters.get("rule_id", ""),
                triggered=False,
                risk_score=0.0,
                severity=RuleResult.score_to_severity(0.0),
                description="No prior location data for comparison",
            )

        assert prior.latitude is not None and prior.longitude is not None
        distance_km = haversine_km(prior.latitude, prior.longitude, txn.latitude, txn.longitude)
        time_diff = txn.timestamp - prior.timestamp
        time_hours = max(time_diff / timedelta(hours=1), 0.01)  # avoid division by zero
        speed_kmh = distance_km / time_hours

        if speed_kmh <= max_speed_kmh:
            return RuleResult(
                rule_type=self.rule_type,
                rule_id=context.rule_parameters.get("rule_id", ""),
                triggered=False,
                risk_score=0.0,
                severity=RuleResult.score_to_severity(0.0),
                description=f"Travel speed plausible: {speed_kmh:.0f} km/h",
            )

        ratio = speed_kmh / max_speed_kmh
        score = min(1.0, 0.6 + (ratio - 1.0) * 0.2)

        return RuleResult(
            rule_type=self.rule_type,
            rule_id=context.rule_parameters.get("rule_id", ""),
            triggered=True,
            risk_score=score,
            severity=RuleResult.score_to_severity(score),
            description=(
                f"Impossible travel detected: {distance_km:.0f}km in {time_hours:.1f}h "
                f"({speed_kmh:.0f} km/h, max: {max_speed_kmh} km/h)"
            ),
            details={
                "distance_km": round(distance_km, 1),
                "time_hours": round(time_hours, 2),
                "speed_kmh": round(speed_kmh, 0),
                "max_speed_kmh": max_speed_kmh,
                "from_location": {"lat": prior.latitude, "lon": prior.longitude},
                "to_location": {"lat": txn.latitude, "lon": txn.longitude},
            },
        )
