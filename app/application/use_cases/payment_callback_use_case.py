import logging

from app.application.dto import (
    CreateOutboxEventDTO,
    PaymentCallbackDTO,
    PaymentCallbackStatus,
)
from app.application.use_cases.send_notification_use_case import SendNotificationUseCase
from app.config import settings
from app.domain.models import OrderStatus, ShippingEventType
from app.exceptions import OrderNotFoundError
from app.infrastructure.uow import UnitOfWork

logger = logging.getLogger(__name__)


class PaymentCallbackUseCase:
    """Use case для обработки запроса на callback от сервиса Payment"""

    def __init__(self, unit_of_work: UnitOfWork, send_notification_use_case: SendNotificationUseCase):
        self._unit_of_work = unit_of_work
        self._send_notification_use_case = send_notification_use_case

    async def __call__(self, callback: PaymentCallbackDTO):
        async with self._unit_of_work() as uow:
            logger.info("Получаем из Payment заказ order_id=%s", callback.order_id)

            order = await uow.orders.get_order_id(order_id=callback.order_id)

            if order is None:
                raise OrderNotFoundError(f"Заказ {callback.order_id} не найден")

            if order.status in (OrderStatus.PAID, OrderStatus.CANCELLED):
                logger.info(
                    "Заказ уже обработан сервисом Payment order_id=%s status=%s",
                    order.id,
                    order.status,
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

            if new_status == OrderStatus.PAID:
                await uow.outbox.create(
                    CreateOutboxEventDTO(
                        topic=settings.kafka_order_events_topic,
                        event_type=ShippingEventType.ORDER_PAID,
                        payload={
                            "event_type": ShippingEventType.ORDER_PAID.value,
                            "order_id": str(updated_order.id),
                            "item_id": str(updated_order.item_id),
                            "quantity": updated_order.quantity,
                            "idempotency_key": str(callback.payment_id),
                        },
                    )
                )
                logger.info("Заказ сохранен в outbox")

            logger.info(
                "Заказ order_id=%s теперь имеет статус status=%s",
                updated_order.id,
                updated_order.status,
            )

            await uow.commit()

            self._send_notification_use_case.dispatch(
                event_payload={
                    "order_id": str(updated_order.id),
                    "reason": callback.error_message,
                },
                event_type="order.paid" if new_status == OrderStatus.PAID else "order.cancelled",
            )

            return updated_order
