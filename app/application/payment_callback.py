import logging

from app.application.dto import PaymentCallbackDTO, PaymentCallbackStatus
from app.domain.models import OrderStatus
from app.exceptions import OrderNotFoundError
from app.infrastructure.uow import UnitOfWork

logger = logging.getLogger(__name__)


class ProcessPaymentCallbackUseCase:
    def __init__(self, unit_of_work: UnitOfWork):
        self._unit_of_work = unit_of_work

    async def __call__(self, callback: PaymentCallbackDTO):
        async with self._unit_of_work() as uow:
            logger.info("Получаем из Paymant заказ order_id=%s", callback.order_id)

            order = await uow.orders.get_order_id(order_id=callback.order_id)

            if order is None:
                raise OrderNotFoundError(f"Заказ {callback.order_id} не найден")

            if order.status in (OrderStatus.PAID, OrderStatus.CANCELLED):
                logger.info(
                    "Заказ уже обработан order_id=%s status=%s", order.id, order.status
                )
                return order

            if callback.status == PaymentCallbackStatus.SUCCEEDED:
                new_status = OrderStatus.PAID
            else:
                new_status = OrderStatus.CANCELLED

            updated_order = await uow.orders.update_status(
                order_id=callback.order_id,
                status=new_status,
            )

            logger.info(
                "Заказ order_id=%s теперь имеет статус status=%s",
                updated_order.id,
                updated_order.status,
            )

            await uow.commit()
            return updated_order
