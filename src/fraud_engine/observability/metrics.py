from __future__ import annotations

from prometheus_client import Counter, Histogram

TRANSACTIONS_INGESTED = Counter(
    "fraud_engine_transactions_ingested_total",
    "Total transactions ingested",
    ["channel", "category"],
)

ALERTS_GENERATED = Counter(
    "fraud_engine_alerts_generated_total",
    "Total fraud alerts generated",
    ["rule_type", "severity"],
)

RULE_EVALUATION_DURATION = Histogram(
    "fraud_engine_rule_evaluation_seconds",
    "Rule evaluation duration in seconds",
    ["rule_type"],
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0],
)

REQUEST_DURATION = Histogram(
    "fraud_engine_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint", "status_code"],
)
