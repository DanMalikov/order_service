import logging

from app.application.dto import CreateOrderDTO
from app.exceptions import NotEnoughQtyError
from app.infrastructure.http_catalog_client import catalog_client
from app.infrastructure.http_payment_client import payments_client
from app.infrastructure.uow import UnitOfWork

logger = logging.getLogger(__name__)

class CreateOrderUseCase:
    def __init__(self, unit_of_work: UnitOfWork):
        self._unit_of_work = unit_of_work
        self._catalog_client = catalog_client
        self._payments_client = payments_client

    async def __call__(self, new_order: CreateOrderDTO):
        async with self._unit_of_work() as uow:

            check_idempotency_key = await uow.orders.get_idempotency_key(idempotency_key=new_order.idempotency_key)

            logger.info("Результат проверки ключа идемпотентности check_idempotency_key=%s", check_idempotency_key)

            if check_idempotency_key is not None:
                return check_idempotency_key

            item = await self._catalog_client.get_item(new_order.item_id)

            if item.available_qty < new_order.quantity:
                logger.exception("Товара недостаточно для заказа. new_order.quantity=%s item.available_qty=%s", new_order.quantity, item.available_qty )

                raise NotEnoughQtyError(
                    f"Недостаточно товара. Заказано - {new_order.quantity}, доступно - {item.available_qty}"
                )

            result = await uow.orders.create(new_order=new_order)

            await uow.commit()

            logger.info("Заказ успешно сформирован")

            return result