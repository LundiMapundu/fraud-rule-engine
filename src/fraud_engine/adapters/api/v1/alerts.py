from __future__ import annotations

import math

from fastapi import APIRouter, Depends, Query

from fraud_engine.adapters.api.dependencies import AuthDep, get_alert_repo
from fraud_engine.adapters.api.v1.schemas import (
    AlertResponse,
    AlertSummaryResponse,
    PaginatedResponse,
    UpdateAlertRequest,
)
from fraud_engine.adapters.persistence.repositories.alert_repo import SqlAlchemyAlertRepository
from fraud_engine.domain.enums import AlertStatus, RiskLevel
from fraud_engine.domain.exceptions import AlertNotFoundError

router = APIRouter(prefix="/alerts", tags=["Alerts"])


@router.get("", response_model=PaginatedResponse)
async def list_alerts(
    _auth: AuthDep,
    repo: SqlAlchemyAlertRepository = Depends(get_alert_repo),
    status: AlertStatus | None = None,
    severity: RiskLevel | None = None,
    customer_id: str | None = None,
    rule_type: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort_by: str = "created_at",
    order: str = Query("desc", pattern="^(asc|desc)$"),
):
    items, total = await repo.list(
        status=status,
        severity=severity,
        customer_id=customer_id,
        rule_type=rule_type,
        start_date=start_date,
        end_date=end_date,
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        order=order,
    )
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


@router.patch("/{alert_id}", response_model=AlertResponse)
async def update_alert_status(
    alert_id: str,
    body: UpdateAlertRequest,
    _auth: AuthDep,
    repo: SqlAlchemyAlertRepository = Depends(get_alert_repo),
):
    alert = await repo.get_by_id(alert_id)
    if alert is None:
        raise AlertNotFoundError(alert_id)

    await repo.update_status(alert_id, body.status)
    alert.status = body.status

    return AlertResponse(
        id=alert.id,
        transaction_id=alert.transaction_id,
        customer_id=alert.customer_id,
        rule_id=alert.rule_id,
        rule_type=alert.rule_type.value,
        risk_score=alert.risk_score,
        severity=alert.severity.value,
        description=alert.description,
        details=alert.details,
        status=alert.status.value,
        created_at=alert.created_at,
        updated_at=alert.updated_at,
    )


@router.get("/summary", response_model=AlertSummaryResponse)
async def get_alert_summary(
    _auth: AuthDep,
    repo: SqlAlchemyAlertRepository = Depends(get_alert_repo),
):
    summary = await repo.get_summary()
    return AlertSummaryResponse(**summary)
