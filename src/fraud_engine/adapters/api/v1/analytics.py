from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from fraud_engine.adapters.api.dependencies import AuthDep, get_analytics_service
from fraud_engine.adapters.api.v1.schemas import AnalyticsOverviewResponse, CustomerProfileResponse
from fraud_engine.application.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/overview", response_model=AnalyticsOverviewResponse)
async def get_overview(
    _auth: AuthDep,
    service: AnalyticsService = Depends(get_analytics_service),
):
    data = await service.get_overview()
    return AnalyticsOverviewResponse(**data)


@router.get("/high-risk-customers", response_model=list[CustomerProfileResponse])
async def get_high_risk_customers(
    _auth: AuthDep,
    service: AnalyticsService = Depends(get_analytics_service),
    limit: int = Query(10, ge=1, le=100),
):
    profiles = await service.get_high_risk_customers(limit=limit)
    return [
        CustomerProfileResponse(
            id=p.id,
            customer_id=p.customer_id,
            composite_risk_score=p.composite_risk_score,
            total_alerts=p.total_alerts,
            critical_alerts=p.critical_alerts,
            high_alerts=p.high_alerts,
            medium_alerts=p.medium_alerts,
            low_alerts=p.low_alerts,
            usual_categories=p.usual_categories,
            avg_transaction_amount=p.avg_transaction_amount,
            total_transactions=p.total_transactions,
        )
        for p in profiles
    ]
