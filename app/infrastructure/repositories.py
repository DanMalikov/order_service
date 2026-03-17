from uuid import UUID

from app.application.dto import CreateOrderDTO, OrderDTO
from app.domain.models import OrderStatus
from app.infrastructure.models import Order
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


class OrderRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(self, new_order: CreateOrderDTO):
        order = Order(
            user_id=new_order.user_id,
            item_id=new_order.item_id,
            quantity=new_order.quantity,
            idempotency_key=new_order.idempotency_key,
            status=OrderStatus.NEW
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

    @staticmethod
    def _convert_to_domain(model_orm: Order) -> OrderDTO:
        return OrderDTO(
            id=model_orm.id,
            user_id=model_orm.user_id,
            quantity=model_orm.quantity,
            item_id=model_orm.item_id,
            status=model_orm.status,
            created_at=model_orm.created_at,
            updated_at=model_orm.updated_at
        )
