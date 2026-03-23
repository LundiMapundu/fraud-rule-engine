from __future__ import annotations

import math

from fastapi import APIRouter, Depends, Query

from fraud_engine.adapters.api.dependencies import AuthDep, get_alert_repo, get_transaction_service
from fraud_engine.adapters.api.v1.schemas import (
    CreateTransactionRequest,
    PaginatedResponse,
    TransactionDetailResponse,
    TransactionResponse,
    TransactionResultResponse,
)
from fraud_engine.adapters.persistence.repositories.alert_repo import SqlAlchemyAlertRepository
from fraud_engine.application.dto import CreateTransactionDTO
from fraud_engine.application.services.transaction_service import TransactionService
from fraud_engine.domain.exceptions import TransactionNotFoundError

router = APIRouter(prefix="/transactions", tags=["Transactions"])


@router.post("", response_model=TransactionResultResponse, status_code=201)
async def ingest_transaction(
    body: CreateTransactionRequest,
    _auth: AuthDep,
    service: TransactionService = Depends(get_transaction_service),
    sync: bool = Query(False, description="Evaluate rules synchronously"),
):
    dto = CreateTransactionDTO(
        customer_id=body.customer_id,
        amount=body.amount,
        currency=body.currency,
        merchant=body.merchant,
        category=body.category,
        channel=body.channel,
        latitude=body.latitude,
        longitude=body.longitude,
        timestamp=body.timestamp,
        card_number_hash=body.card_number_hash,
        metadata=body.metadata,
    )
    result = await service.ingest(dto, sync=sync)
    return TransactionResultResponse(
        transaction_id=result.transaction_id,
        is_flagged=result.is_flagged,
        alerts=result.alerts,
        composite_risk_score=result.composite_risk_score,
        severity=result.severity,
    )


@router.get("", response_model=PaginatedResponse)
async def list_transactions(
    _auth: AuthDep,
    service: TransactionService = Depends(get_transaction_service),
    customer_id: str | None = None,
    category: str | None = None,
    min_amount: float | None = None,
    max_amount: float | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    is_flagged: bool | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort_by: str = "timestamp",
    order: str = Query("desc", pattern="^(asc|desc)$"),
):
    items, total = await service.list_transactions(
        customer_id=customer_id,
        category=category,
        min_amount=min_amount,
        max_amount=max_amount,
        start_date=start_date,
        end_date=end_date,
        is_flagged=is_flagged,
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        order=order,
    )
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


@router.get("/{transaction_id}", response_model=TransactionDetailResponse)
async def get_transaction(
    transaction_id: str,
    _auth: AuthDep,
    service: TransactionService = Depends(get_transaction_service),
    alert_repo: SqlAlchemyAlertRepository = Depends(get_alert_repo),
):
    txn = await service.get_transaction(transaction_id)
    if txn is None:
        raise TransactionNotFoundError(transaction_id)

    alerts = await alert_repo.get_by_transaction(transaction_id)
    return TransactionDetailResponse(
        id=txn.id,
        customer_id=txn.customer_id,
        amount=txn.amount,
        currency=txn.currency,
        merchant=txn.merchant,
        category=txn.category.value,
        channel=txn.channel.value,
        latitude=txn.latitude,
        longitude=txn.longitude,
        timestamp=txn.timestamp,
        is_flagged=txn.is_flagged,
        created_at=txn.created_at,
        alerts=[
            {
                "id": a.id,
                "rule_type": a.rule_type.value,
                "severity": a.severity.value,
                "description": a.description,
                "risk_score": a.risk_score,
                "status": a.status.value,
            }
            for a in alerts
        ],
    )
