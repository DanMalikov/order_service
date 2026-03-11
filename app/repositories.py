from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Order, OrderStatus


class OrderRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, order_id: UUID) -> Order | None:
        result = await self.session.execute(select(Order).where(Order.id == order_id))
        return result.scalar_one_or_none()

    async def get_by_idempotency_key(self, idempotency_key: str) -> Order | None:
        result = await self.session.execute(
            select(Order).where(Order.idempotency_key == idempotency_key)
        )
        return result.scalar_one_or_none()

    async def create(
        self, user_id: str, item_id: UUID, quantity: int, idempotency_key: str
    ) -> Order:
        order = Order(
            user_id=user_id,
            item_id=item_id,
            quantity=quantity,
            idempotency_key=idempotency_key,
            status=OrderStatus.NEW,
        )
        self.session.add(order)
        await self.session.flush()
        await self.session.refresh(order)
        return order
