from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.dto import (
    CreateInboxEventDTO,
    CreateOrderDTO,
    CreateOutboxEventDTO,
    OrderDTO,
)
from app.domain.models import (
    InboxEvent,
    InboxEventStatus,
    OrderStatus,
    OutboxEvent,
    OutboxEventStatus,
)
from app.exceptions import DuplicateInboxEventError
from app.infrastructure.models import InboxEventORM, Order, OutboxEventORM


class OrderRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(self, new_order: CreateOrderDTO):
        order = Order(
            user_id=new_order.user_id,
            item_id=new_order.item_id,
            quantity=new_order.quantity,
            idempotency_key=new_order.idempotency_key,
            status=OrderStatus.NEW,
        )

        self._session.add(order)
        await self._session.flush()

        return self._convert_to_domain(order)

    async def get_order_id(self, order_id: UUID):
        result = await self._session.execute(select(Order).where(Order.id == order_id))
        order = result.scalar_one_or_none()
        if order is None:
            return None
        return self._convert_to_domain(order)

    async def get_idempotency_key(self, idempotency_key: str):
        result = await self._session.execute(
            select(Order).where(Order.idempotency_key == idempotency_key)
        )
        order = result.scalar_one_or_none()
        if order is None:
            return None
        return self._convert_to_domain(order)

    async def update_status(self, order_id: UUID, status: OrderStatus):
        result = await self._session.execute(select(Order).where(Order.id == order_id))
        order = result.scalar_one_or_none()
        if order is None:
            return None

        order.status = status
        await self._session.flush()
        await self._session.refresh(order)
        return self._convert_to_domain(order)

    @staticmethod
    def _convert_to_domain(model_orm: Order) -> OrderDTO:
        return OrderDTO(
            id=model_orm.id,
            user_id=model_orm.user_id,
            quantity=model_orm.quantity,
            item_id=model_orm.item_id,
            status=model_orm.status,
            created_at=model_orm.created_at,
            updated_at=model_orm.updated_at,
        )


class OutboxRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(self, event: CreateOutboxEventDTO) -> OutboxEvent:
        row = OutboxEventORM(
            topic=event.topic,
            event_type=event.event_type,
            payload=event.payload,
            status=OutboxEventStatus.PENDING,
        )
        self._session.add(row)
        await self._session.flush()
        await self._session.refresh(row)
        return self._convert_outbox(row)

    async def get_pending_events_for_update(
        self, limit: int = 100
    ) -> list[OutboxEvent]:
        stmt = (
            select(OutboxEventORM)
            .where(OutboxEventORM.status == OutboxEventStatus.PENDING)
            .order_by(OutboxEventORM.created_at)
            .limit(limit)
            .with_for_update(skip_locked=True)
        )
        result = await self._session.execute(stmt)
        rows = result.scalars().all()
        return [self._convert_outbox(row) for row in rows]

    async def mark_as_sent(self, event_id: UUID) -> None:
        stmt = (
            update(OutboxEventORM)
            .where(OutboxEventORM.id == event_id)
            .values(status=OutboxEventStatus.SENT, updated_at=func.now())
        )
        await self._session.execute(stmt)

    @staticmethod
    def _convert_outbox(row: OutboxEventORM) -> OutboxEvent:
        return OutboxEvent(
            id=row.id,
            topic=row.topic,
            event_type=row.event_type,
            payload=row.payload,
            status=row.status,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )


class InboxRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(self, event: CreateInboxEventDTO) -> InboxEvent:
        stmt = (
            insert(InboxEventORM)
            .values(
                event_id=event.event_id,
                event_type=event.event_type,
                payload=event.payload,
                status=InboxEventStatus.PENDING,
            )
            .on_conflict_do_nothing(index_elements=["event_id"])
            .returning(InboxEventORM)
        )
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        if row is None:
            raise DuplicateInboxEventError(f"Событие {event.event_id} уже сохранено")
        return self._convert_inbox(row)

    async def get_pending_events_for_update(self, limit: int = 100) -> list[InboxEvent]:
        stmt = (
            select(InboxEventORM)
            .where(InboxEventORM.status == InboxEventStatus.PENDING)
            .order_by(InboxEventORM.created_at)
            .limit(limit)
            .with_for_update(skip_locked=True)
        )
        result = await self._session.execute(stmt)
        rows = result.scalars().all()
        return [self._convert_inbox(row) for row in rows]

    async def mark_as_processed(self, event_id: str) -> None:
        stmt = (
            update(InboxEventORM)
            .where(InboxEventORM.event_id == event_id)
            .values(status=InboxEventStatus.PROCESSED, processed_at=func.now())
        )
        await self._session.execute(stmt)

    @staticmethod
    def _convert_inbox(row: InboxEventORM) -> InboxEvent:
        return InboxEvent(
            id=row.id,
            event_id=row.event_id,
            event_type=row.event_type,
            payload=row.payload,
            status=row.status,
            created_at=row.created_at,
            processed_at=row.processed_at,
        )
