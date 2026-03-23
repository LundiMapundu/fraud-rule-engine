from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy import Select, desc, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from fraud_engine.adapters.persistence.orm import TransactionModel
from fraud_engine.domain.enums import TransactionCategory, TransactionChannel
from fraud_engine.domain.models import Transaction


class SqlAlchemyTransactionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _to_domain(self, model: TransactionModel) -> Transaction:
        return Transaction(
            id=model.id,
            customer_id=model.customer_id,
            amount=model.amount,
            currency=model.currency,
            merchant=model.merchant,
            category=TransactionCategory(model.category),
            channel=TransactionChannel(model.channel),
            latitude=model.latitude,
            longitude=model.longitude,
            timestamp=model.timestamp,
            card_number_hash=model.card_number_hash,
            metadata=model.metadata_,
            is_flagged=model.is_flagged,
            created_at=model.created_at,
        )

    def _to_model(self, txn: Transaction) -> TransactionModel:
        return TransactionModel(
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
            card_number_hash=txn.card_number_hash,
            metadata_=txn.metadata,
            is_flagged=txn.is_flagged,
            created_at=txn.created_at,
        )

    async def save(self, transaction: Transaction) -> None:
        self._session.add(self._to_model(transaction))
        await self._session.flush()

    async def get_by_id(self, transaction_id: str) -> Transaction | None:
        result = await self._session.get(TransactionModel, transaction_id)
        return self._to_domain(result) if result else None

    async def list(
        self,
        customer_id: str | None = None,
        category: str | None = None,
        min_amount: float | None = None,
        max_amount: float | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        is_flagged: bool | None = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "timestamp",
        order: str = "desc",
    ) -> tuple[list[Transaction], int]:
        query: Select = select(TransactionModel)  # type: ignore[type-arg]
        count_query = select(func.count()).select_from(TransactionModel)

        if customer_id:
            query = query.where(TransactionModel.customer_id == customer_id)
            count_query = count_query.where(TransactionModel.customer_id == customer_id)
        if category:
            query = query.where(TransactionModel.category == category)
            count_query = count_query.where(TransactionModel.category == category)
        if min_amount is not None:
            query = query.where(TransactionModel.amount >= min_amount)
            count_query = count_query.where(TransactionModel.amount >= min_amount)
        if max_amount is not None:
            query = query.where(TransactionModel.amount <= max_amount)
            count_query = count_query.where(TransactionModel.amount <= max_amount)
        if start_date:
            query = query.where(TransactionModel.timestamp >= start_date)
            count_query = count_query.where(TransactionModel.timestamp >= start_date)
        if end_date:
            query = query.where(TransactionModel.timestamp <= end_date)
            count_query = count_query.where(TransactionModel.timestamp <= end_date)
        if is_flagged is not None:
            query = query.where(TransactionModel.is_flagged == is_flagged)
            count_query = count_query.where(TransactionModel.is_flagged == is_flagged)

        sort_col = getattr(TransactionModel, sort_by, TransactionModel.timestamp)
        query = query.order_by(desc(sort_col) if order == "desc" else sort_col)

        total_result = await self._session.execute(count_query)
        total = total_result.scalar() or 0

        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)

        result = await self._session.execute(query)
        models = result.scalars().all()
        return [self._to_domain(m) for m in models], total

    async def get_recent(
        self, customer_id: str, limit: int = 100, hours: int = 24
    ) -> list[Transaction]:
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        query = (
            select(TransactionModel)
            .where(
                TransactionModel.customer_id == customer_id,
                TransactionModel.timestamp >= cutoff,
            )
            .order_by(desc(TransactionModel.timestamp))
            .limit(limit)
        )
        result = await self._session.execute(query)
        return [self._to_domain(m) for m in result.scalars().all()]

    async def flag(self, transaction_id: str) -> None:
        stmt = (
            update(TransactionModel)
            .where(TransactionModel.id == transaction_id)
            .values(is_flagged=True)
        )
        await self._session.execute(stmt)
        await self._session.flush()
