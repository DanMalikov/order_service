import logging
from decimal import Decimal

from app.application.dto import CreateOrderDTO
from app.application.use_cases.send_notification_use_case import SendNotificationUseCase
from app.config import settings
from app.domain.models import OrderStatus
from app.exceptions import NotEnoughQtyError, PaymentServiceUnavailableError
from app.infrastructure.http_clients.http_catalog_client import catalog_client
from app.infrastructure.http_clients.http_payment_client import (
    CreatePaymentRequest,
    payments_client,
)
from app.infrastructure.uow import UnitOfWork

logger = logging.getLogger(__name__)


class CreateOrderUseCase:
    """Use case для обработки создания заказа и отправки заказа в сервис Payment"""

    def __init__(self, unit_of_work: UnitOfWork, send_notification_use_case: SendNotificationUseCase):
        self._unit_of_work = unit_of_work
        self._catalog_client = catalog_client
        self._payments_client = payments_client
        self._send_notification_use_case = send_notification_use_case

    async def __call__(self, new_order: CreateOrderDTO):
        async with self._unit_of_work() as uow:
            check_idempotency_key = await uow.orders.get_idempotency_key(
                idempotency_key=new_order.idempotency_key
            )

            logger.info(
                "Результат проверки ключа идемпотентности check_idempotency_key=%s",
                check_idempotency_key,
            )

            if check_idempotency_key is not None:
                return check_idempotency_key

            item = await self._catalog_client.get_item(new_order.item_id)

            if item.available_qty < new_order.quantity:
                logger.exception(
                    "Товара недостаточно для заказа. new_order.quantity=%s item.available_qty=%s",
                    new_order.quantity,
                    item.available_qty,
                )

                raise NotEnoughQtyError(
                    f"Недостаточно товара. Заказано - {new_order.quantity}, доступно - {item.available_qty}"
                )

            created_order = await uow.orders.create(new_order=new_order)

            amount = Decimal(item.price) * Decimal(new_order.quantity)

            try:
                await self._payments_client.create_payment(
                    CreatePaymentRequest(
                        order_id=created_order.id,
                        amount=amount,
                        callback_url=settings.callback_url,
                        idempotency_key=new_order.idempotency_key,
                    )
                )
            except PaymentServiceUnavailableError:
                cancelled_order = await uow.orders.update_status(
                    order_id=created_order.id,
                    status=OrderStatus.CANCELLED,
                )
                await uow.commit()
                self._send_notification_use_case.dispatch(
                    event_payload={
                        "order_id": str(cancelled_order.id),
                        "reason": "Не удалось создать платеж",
                    },
                    event_type="order.cancelled",
                )
                return cancelled_order

            await uow.commit()

            self._send_notification_use_case.dispatch(
                event_payload={"order_id": str(created_order.id)},
                event_type="order.new",
            )

            logger.info("Заказ order_id=%s успешно сформирован", created_order.id)

            return created_order
