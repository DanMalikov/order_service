import logging
from uuid import UUID

import httpx
from pydantic import BaseModel

from app.config import settings
from app.exceptions import NotificationsServiceUnavailableError

logger = logging.getLogger(__name__)


class CreateNotificationRequest(BaseModel):
    message: str
    reference_id: UUID
    idempotency_key: str


class NotificationResponse(BaseModel):
    id: UUID
    user_id: str
    message: str
    reference_id: UUID


class NotificationsClient:
    """Клиент для отправки уведомлений в Notifications Service."""

    def __init__(self) -> None:
        self._client = httpx.AsyncClient(
            base_url=settings.capashino_base_url,
            headers={"X-API-Key": settings.api_key},
            timeout=10.0,
        )

    async def send_notification(
        self, notification: CreateNotificationRequest
    ) -> NotificationResponse:
        url = "/api/notifications"
        payload = notification.model_dump(mode="json")

        logger.info(
            "Отправляем уведомление reference_id=%s idempotency_key=%s",
            notification.reference_id,
            notification.idempotency_key,
        )

        try:
            response = await self._client.post(url, json=payload)
        except httpx.RequestError as exc:
            logger.exception(
                "Запрос в Notifications сломался reference_id=%s",
                notification.reference_id,
            )
            raise NotificationsServiceUnavailableError(
                "Не удалось отправить уведомление в сервис Notifications"
            ) from exc

        logger.info(
            "Ответ от Notifications reference_id=%s status_code=%s response_text=%s",
            notification.reference_id,
            response.status_code,
            response.text,
        )

        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise NotificationsServiceUnavailableError(
                "Ошибка при работе с Notifications"
            ) from exc

        return NotificationResponse.model_validate(response.json())


notifications_client = NotificationsClient()
