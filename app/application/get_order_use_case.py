import logging
from uuid import UUID

from app.exceptions import OrderNotFoundError
from app.infrastructure.uow import UnitOfWork

logger = logging.getLogger(__name__)


class GetOrderUseCase:
    """Use case для обработки запроса заказа по id"""
    def __init__(self, unit_of_work: UnitOfWork):
        self._unit_of_work = unit_of_work

    async def __call__(self, order_id: UUID):
        async with self._unit_of_work() as uow:
            result = await uow.orders.get_order_id(order_id=order_id)

            if result is None:
                logger.exception("Заказ order_id=%s не найден", order_id)

                raise OrderNotFoundError(f"Заказ {order_id} не найден")

            logger.info("Получен заказ order_id=%s", result.id)

            return result
