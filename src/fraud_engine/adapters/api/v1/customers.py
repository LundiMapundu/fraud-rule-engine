from __future__ import annotations

import math

from fastapi import APIRouter, Depends, Query

from fraud_engine.adapters.api.dependencies import AuthDep, get_customer_service
from fraud_engine.adapters.api.v1.schemas import (
    AlertResponse,
    CustomerProfileResponse,
    PaginatedResponse,
    TransactionResponse,
)
from fraud_engine.application.services.customer_service import CustomerService

router = APIRouter(prefix="/customers", tags=["Customers"])


@router.get("/{customer_id}/profile", response_model=CustomerProfileResponse)
async def get_customer_profile(
    customer_id: str,
    _auth: AuthDep,
    service: CustomerService = Depends(get_customer_service),
):
    profile = await service.get_profile(customer_id)
    return CustomerProfileResponse(
        id=profile.id,
        customer_id=profile.customer_id,
        composite_risk_score=profile.composite_risk_score,
        total_alerts=profile.total_alerts,
        critical_alerts=profile.critical_alerts,
        high_alerts=profile.high_alerts,
        medium_alerts=profile.medium_alerts,
        low_alerts=profile.low_alerts,
        usual_categories=profile.usual_categories,
        avg_transaction_amount=profile.avg_transaction_amount,
        total_transactions=profile.total_transactions,
    )


@router.get("/{customer_id}/transactions", response_model=PaginatedResponse)
async def get_customer_transactions(
    customer_id: str,
    _auth: AuthDep,
    service: CustomerService = Depends(get_customer_service),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    items, total = await service.get_transactions(customer_id, page=page, page_size=page_size)
    return PaginatedResponse(
        items=[
            TransactionResponse(
                id=t.id,
                customer_id=t.customer_id,
                amount=t.amount,
                currency=t.currency,
                merchant=t.merchant,
                category=t.category.value,
                channel=t.channel.value,
                latitude=t.latitude,
                longitude=t.longitude,
                timestamp=t.timestamp,
                is_flagged=t.is_flagged,
                created_at=t.created_at,
            )
            for t in items
        ],
        total=total,
        page=page,
        page_size=page_size,
        pages=math.ceil(total / page_size) if total > 0 else 0,
    )


@router.get("/{customer_id}/alerts", response_model=PaginatedResponse)
async def get_customer_alerts(
    customer_id: str,
    _auth: AuthDep,
    service: CustomerService = Depends(get_customer_service),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    items, total = await service.get_alerts(customer_id, page=page, page_size=page_size)
    return PaginatedResponse(
        items=[
            AlertResponse(
                id=a.id,
                transaction_id=a.transaction_id,
                customer_id=a.customer_id,
                rule_id=a.rule_id,
                rule_type=a.rule_type.value,
                risk_score=a.risk_score,
                severity=a.severity.value,
                description=a.description,
                details=a.details,
                status=a.status.value,
                created_at=a.created_at,
                updated_at=a.updated_at,
            )
            for a in items
        ],
        total=total,
        page=page,
        page_size=page_size,
        pages=math.ceil(total / page_size) if total > 0 else 0,
    )
