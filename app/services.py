from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.clients import CatalogClient
from app.exceptions import NotEnoughQtyError, OrderNotFoundError
from app.repositories import OrderRepository


class OrderService:
    def __init__(self, session: AsyncSession, catalog_client: CatalogClient):
        self.session = session
        self.catalog_client = catalog_client
        self.orders = OrderRepository(session)

    async def create_order(
        self, user_id: str, item_id: UUID, quantity: int, idempotency_key: UUID
    ):
        existing = await self.orders.get_by_idempotency_key(idempotency_key)
        if existing is not None:
            return existing, False

        await self.check_available_qty(item_id=item_id, quantity=quantity)
        order = await self.orders.create(
            user_id=user_id,
            item_id=item_id,
            quantity=quantity,
            idempotency_key=idempotency_key,
        )
        await self.session.commit()
        return order, True

    async def get_order(self, order_id: UUID):
        order = await self.orders.get_by_id(order_id)
        if order is None:
            raise OrderNotFoundError(f"Заказ {order_id} не найден")
        return order

    async def check_available_qty(self, item_id: UUID, quantity: int) -> None:
        item = await self.catalog_client.get_item(item_id)
        if item.available_qty < quantity:
            raise NotEnoughQtyError(
                f"Ошибка. Заказано - {quantity}, доступно - {item.available_qty}"
            )
