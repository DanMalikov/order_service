import logging
from uuid import UUID

from app.exceptions import OrderNotFoundError
from app.infrastructure.uow import UnitOfWork

logger = logging.getLogger(__name__)


class GetOrderUseCase:
    def __init__(self, unit_of_work: UnitOfWork):
        self._unit_of_work = unit_of_work

    async def __call__(self, order_id: UUID):
        async with self._unit_of_work() as uow:
            result = await uow.orders.get_order_id(order_id=order_id)

            logger.info("Получен заказ result=%s", result)

            if result is None:

                logger.exception("Заказ не найден")

                raise OrderNotFoundError(f"Заказ {order_id} не найден")

            return result
