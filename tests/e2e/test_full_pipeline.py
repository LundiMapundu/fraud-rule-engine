import pytest
from httpx import AsyncClient

from fraud_engine.config import settings

API_KEY_HEADER = {"X-API-Key": settings.api_key}


@pytest.mark.asyncio
async def test_full_fraud_detection_pipeline(async_client: AsyncClient):
    """End-to-end test: create rules, submit transactions, verify alerts."""

    # 1. Create rules
    rules = [
        {
            "name": "E2E High Value",
            "rule_type": "high_value",
            "parameters": {"threshold_zar": 5000},
            "risk_weight": 1.2,
        },
        {
            "name": "E2E Time Anomaly",
            "rule_type": "time_anomaly",
            "parameters": {"unusual_hour_start": 1, "unusual_hour_end": 5},
            "risk_weight": 0.8,
        },
    ]

    for rule in rules:
        resp = await async_client.post("/api/v1/rules", json=rule, headers=API_KEY_HEADER)
        assert resp.status_code == 201

    # 2. Submit a high-value transaction (sync)
    txn_resp = await async_client.post(
        "/api/v1/transactions?sync=true",
        json={
            "customer_id": "E2E_CUST001",
            "amount": 25000.00,
            "currency": "ZAR",
            "merchant": "Test Merchant",
            "category": "electronics",
            "channel": "online",
        },
        headers=API_KEY_HEADER,
    )
    assert txn_resp.status_code == 201
    txn_data = txn_resp.json()
    assert txn_data["is_flagged"]
    txn_id = txn_data["transaction_id"]

    # 3. Verify transaction is flagged
    detail_resp = await async_client.get(f"/api/v1/transactions/{txn_id}", headers=API_KEY_HEADER)
    assert detail_resp.status_code == 200
    assert detail_resp.json()["is_flagged"]

    # 4. Check alerts exist
    alerts_resp = await async_client.get("/api/v1/alerts", headers=API_KEY_HEADER)
    assert alerts_resp.status_code == 200
    alerts = alerts_resp.json()["items"]
    matching_alerts = [a for a in alerts if a["transaction_id"] == txn_id]
    assert len(matching_alerts) > 0

    # 5. Resolve an alert
    alert_id = matching_alerts[0]["id"]
    patch_resp = await async_client.patch(
        f"/api/v1/alerts/{alert_id}",
        json={"status": "resolved"},
        headers=API_KEY_HEADER,
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["status"] == "resolved"

    # 6. Check analytics overview
    overview_resp = await async_client.get("/api/v1/analytics/overview", headers=API_KEY_HEADER)
    assert overview_resp.status_code == 200
    assert overview_resp.json()["total_alerts"] > 0
