import asyncio
import logging
from uuid import UUID

from app.infrastructure.http_clients.http_notifications_client import (
    CreateNotificationRequest,
    NotificationsClient,
)

logger = logging.getLogger(__name__)


class SendNotificationUseCase:
    """Централизованная отправка уведомлений по событиям заказа."""

    def __init__(self, notifications_api: NotificationsClient):
        self._notifications_api = notifications_api
        self._templates = {
            "order.new": "NEW: Ваш заказ создан и ожидает оплаты",
            "order.paid": "PAID: Ваш заказ успешно оплачен и готов к отправке",
            "order.shipped": "SHIPPED: Ваш заказ отправлен в доставку.",
            "order.cancelled": "CANCELLED: Ваш заказ отменен.",
        }

    async def execute(self, event_payload: dict, event_type: str) -> None:
        if event_type not in self._templates:
            logger.warning("Неизвестный тип события для уведомления: %s", event_type)
            return

        message = self._templates.get(event_type)
        if event_type == "order.cancelled":
            reason = event_payload.get("reason")
            if reason:
                message = f"{message} Причина: {reason}"

        order_id = event_payload.get("order_id")
        if not order_id:
            logger.error("В payload отсутствует order_id для события %s", event_type)
            return

        idempotency_key = event_payload.get("idempotency_key")
        if not idempotency_key:
            idempotency_key = f"notification:{order_id}:{event_type}"

        try:
            await self._notifications_api.send_notification(
                CreateNotificationRequest(
                    message=message,
                    reference_id=UUID(str(order_id)),
                    idempotency_key=idempotency_key,
                )
            )
            logger.info(
                "Уведомление успешно отправлено. order_id=%s event_type=%s",
                order_id,
                event_type,
            )
        except Exception:
            logger.exception(
                "Не удалось отправить уведомление. order_id=%s event_type=%s",
                order_id,
                event_type,
            )

    def dispatch(self, event_payload: dict, event_type: str) -> asyncio.Task:
        """Создание отдельной задачи, чтобы не блокировать обработку заказа"""
        return asyncio.create_task(
            self.execute(event_payload=event_payload, event_type=event_type)
        )
