import asyncio
import logging
from uuid import UUID

from app.application.use_cases.send_notification_use_case import SendNotificationUseCase
from app.domain.models import OrderStatus, ShippingEventType
from app.infrastructure.uow import UnitOfWork

logger = logging.getLogger(__name__)


class ProcessInboxEventsUseCase:
    """Реализация паттерна Inbox"""

    def __init__(
        self,
        unit_of_work: UnitOfWork,
        send_notification_use_case: SendNotificationUseCase,
        batch_size: int = 100,
        poll_interval: float = 5.0,
    ):
        self._unit_of_work = unit_of_work
        self._send_notification_use_case = send_notification_use_case
        self._batch_size = batch_size
        self._poll_interval = poll_interval
        self._is_running = False

    def stop(self) -> None:
        self._is_running = False

    async def process_batch(self) -> int:
        processed = 0
        notifications_to_send: list[tuple[dict, str]] = []
        async with self._unit_of_work() as uow:
            events = await uow.inbox.get_pending_events_for_update(
                limit=self._batch_size
            )
            if not events:
                logger.info("events для Inbox не найдено. Уходим на ожидание")
                return 0

            logger.info("Количество найденных events в Inbox = %s", len(events))

            for event in events:
                order_id_raw = event.payload.get("order_id")
                if order_id_raw is None:
                    logger.warning(
                        "В событии нет order_id, event_id=%s", event.event_id
                    )
                    await uow.inbox.mark_as_processed(event.event_id)
                    processed += 1
                    continue

                order = await uow.orders.get_order_id(UUID(str(order_id_raw)))
                if order is None:
                    logger.warning(
                        "Заказ %s не найден, пропускаем event_id=%s",
                        order_id_raw,
                        event.event_id,
                    )
                    await uow.inbox.mark_as_processed(event.event_id)
                    processed += 1
                    continue

                logger.info("В Inbox найден объект с id = %s", order.id)

                if event.event_type == ShippingEventType.ORDER_SHIPPED:
                    if order.status != OrderStatus.SHIPPED:
                        await uow.orders.update_status(order.id, OrderStatus.SHIPPED)
                        notifications_to_send.append(
                            (
                                {"order_id": str(order.id)},
                                "order.shipped",
                            )
                        )
                        logger.info(
                            "Объект %s получил статус %s",
                            order.id,
                            OrderStatus.SHIPPED,
                        )
                elif event.event_type == ShippingEventType.ORDER_CANCELLED:
                    if order.status != OrderStatus.CANCELLED:
                        cancel_reason = event.payload.get("reason")
                        await uow.orders.update_status(order.id, OrderStatus.CANCELLED)
                        notifications_to_send.append(
                            (
                                {"order_id": str(order.id), "reason": cancel_reason},
                                "order.cancelled",
                            )
                        )
                        logger.info(
                            "Объект %s получил статус %s",
                            order.id,
                            OrderStatus.CANCELLED,
                        )
                else:
                    logger.warning(
                        "Неподдерживаемый тип события %s, event_id=%s",
                        event.event_type,
                        event.event_id,
                    )

                await uow.inbox.mark_as_processed(event.event_id)
                processed += 1

            await uow.commit()

        for event_payload, event_type in notifications_to_send:
            self._send_notification_use_case.dispatch(
                event_payload=event_payload,
                event_type=event_type,
            )

        return processed

    async def run(self) -> None:
        self._is_running = True
        logger.info("Inbox worker запущен")
        while self._is_running:
            try:
                processed = await self.process_batch()
                if processed == 0:
                    await asyncio.sleep(self._poll_interval)
            except Exception:
                logger.exception("Ошибка в цикле Inbox worker")
                await asyncio.sleep(self._poll_interval)
