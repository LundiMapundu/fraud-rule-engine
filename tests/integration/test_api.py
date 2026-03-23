import pytest
from httpx import AsyncClient

from fraud_engine.config import settings

API_KEY_HEADER = {"X-API-Key": settings.api_key}


@pytest.mark.asyncio
async def test_health(async_client: AsyncClient):
    response = await async_client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_create_transaction_requires_auth(async_client: AsyncClient):
    response = await async_client.post("/api/v1/transactions", json={})
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_create_and_get_transaction(async_client: AsyncClient):
    payload = {
        "customer_id": "CUST001",
        "amount": 1500.00,
        "currency": "ZAR",
        "merchant": "Pick n Pay",
        "category": "groceries",
        "channel": "pos",
        "latitude": -33.9249,
        "longitude": 18.4241,
    }
    response = await async_client.post(
        "/api/v1/transactions?sync=true", json=payload, headers=API_KEY_HEADER
    )
    assert response.status_code == 201
    data = response.json()
    assert data["transaction_id"]

    # Get transaction
    txn_id = data["transaction_id"]
    response = await async_client.get(f"/api/v1/transactions/{txn_id}", headers=API_KEY_HEADER)
    assert response.status_code == 200
    assert response.json()["id"] == txn_id


@pytest.mark.asyncio
async def test_create_rule(async_client: AsyncClient):
    payload = {
        "name": "Test High Value Rule",
        "rule_type": "high_value",
        "parameters": {"threshold_zar": 50000},
        "risk_weight": 1.0,
        "description": "Test rule",
    }
    response = await async_client.post("/api/v1/rules", json=payload, headers=API_KEY_HEADER)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test High Value Rule"
    assert data["rule_type"] == "high_value"


@pytest.mark.asyncio
async def test_high_value_transaction_flagged(async_client: AsyncClient):
    # Create the rule first
    rule_payload = {
        "name": "High Value Flag",
        "rule_type": "high_value",
        "parameters": {"threshold_zar": 10000},
        "risk_weight": 1.0,
    }
    await async_client.post("/api/v1/rules", json=rule_payload, headers=API_KEY_HEADER)

    # Submit a high-value transaction
    txn_payload = {
        "customer_id": "CUST002",
        "amount": 75000.00,
        "currency": "ZAR",
        "merchant": "Luxury Store",
        "category": "electronics",
        "channel": "pos",
    }
    response = await async_client.post(
        "/api/v1/transactions?sync=true", json=txn_payload, headers=API_KEY_HEADER
    )
    assert response.status_code == 201
    data = response.json()
    assert data["is_flagged"]
    assert len(data["alerts"]) > 0
    assert data["composite_risk_score"] > 0


@pytest.mark.asyncio
async def test_list_transactions(async_client: AsyncClient):
    response = await async_client.get("/api/v1/transactions", headers=API_KEY_HEADER)
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert "page" in data


@pytest.mark.asyncio
async def test_list_alerts(async_client: AsyncClient):
    response = await async_client.get("/api/v1/alerts", headers=API_KEY_HEADER)
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
