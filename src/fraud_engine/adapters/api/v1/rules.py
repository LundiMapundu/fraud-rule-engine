from __future__ import annotations

from fastapi import APIRouter, Depends

from fraud_engine.adapters.api.dependencies import (
    AuthDep,
    get_rule_service,
    get_transaction_service,
)
from fraud_engine.adapters.api.v1.schemas import (
    CreateRuleRequest,
    CreateTransactionRequest,
    RuleResponse,
    TransactionResultResponse,
    UpdateRuleRequest,
)
from fraud_engine.application.dto import CreateRuleDTO, CreateTransactionDTO, UpdateRuleDTO
from fraud_engine.application.services.rule_management_service import RuleManagementService
from fraud_engine.application.services.transaction_service import TransactionService

router = APIRouter(prefix="/rules", tags=["Rules"])


def _rule_to_response(rule) -> RuleResponse:  # type: ignore[no-untyped-def]
    return RuleResponse(
        id=rule.id,
        name=rule.name,
        rule_type=rule.rule_type.value,
        is_enabled=rule.is_enabled,
        parameters=rule.parameters,
        risk_weight=rule.risk_weight,
        description=rule.description,
        created_at=rule.created_at,
        updated_at=rule.updated_at,
    )


@router.post("", response_model=RuleResponse, status_code=201)
async def create_rule(
    body: CreateRuleRequest,
    _auth: AuthDep,
    service: RuleManagementService = Depends(get_rule_service),
):
    dto = CreateRuleDTO(
        name=body.name,
        rule_type=body.rule_type,
        parameters=body.parameters,
        risk_weight=body.risk_weight,
        is_enabled=body.is_enabled,
        description=body.description,
    )
    rule = await service.create_rule(dto)
    return _rule_to_response(rule)


@router.get("", response_model=list[RuleResponse])
async def list_rules(
    _auth: AuthDep,
    service: RuleManagementService = Depends(get_rule_service),
):
    rules = await service.list_rules()
    return [_rule_to_response(r) for r in rules]


@router.get("/{rule_id}", response_model=RuleResponse)
async def get_rule(
    rule_id: str,
    _auth: AuthDep,
    service: RuleManagementService = Depends(get_rule_service),
):
    rule = await service.get_rule(rule_id)
    return _rule_to_response(rule)


@router.put("/{rule_id}", response_model=RuleResponse)
async def update_rule(
    rule_id: str,
    body: UpdateRuleRequest,
    _auth: AuthDep,
    service: RuleManagementService = Depends(get_rule_service),
):
    dto = UpdateRuleDTO(
        name=body.name,
        parameters=body.parameters,
        risk_weight=body.risk_weight,
        is_enabled=body.is_enabled,
        description=body.description,
    )
    rule = await service.update_rule(rule_id, dto)
    return _rule_to_response(rule)


@router.delete("/{rule_id}", status_code=204)
async def delete_rule(
    rule_id: str,
    _auth: AuthDep,
    service: RuleManagementService = Depends(get_rule_service),
):
    await service.delete_rule(rule_id)


@router.post("/{rule_id}/test", response_model=TransactionResultResponse)
async def test_rule(
    rule_id: str,
    body: CreateTransactionRequest,
    _auth: AuthDep,
    rule_service: RuleManagementService = Depends(get_rule_service),
    txn_service: TransactionService = Depends(get_transaction_service),
):
    """Dry-run a single rule against a sample transaction (sync evaluation)."""
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
    result = await txn_service.ingest(dto, sync=True)
    return TransactionResultResponse(
        transaction_id=result.transaction_id,
        is_flagged=result.is_flagged,
        alerts=result.alerts,
        composite_risk_score=result.composite_risk_score,
        severity=result.severity,
    )
