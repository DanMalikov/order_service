import logging
from uuid import UUID

import httpx
from pydantic import BaseModel
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.config import settings

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

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=0.5, min=0.5, max=3),
        retry=retry_if_exception_type((httpx.RequestError, httpx.HTTPStatusError)),
        reraise=True,
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
        except httpx.RequestError:
            logger.exception(
                "Сетевая ошибка при запросе в Notifications reference_id=%s",
                notification.reference_id,
            )
            raise

        logger.info(
            "Ответ от Notifications reference_id=%s status_code=%s response_text=%s",
            notification.reference_id,
            response.status_code,
            response.text,
        )

        try:
            response.raise_for_status()
        except httpx.HTTPStatusError:
            logger.exception(
                "Notifications вернул ошибку reference_id=%s status_code=%s",
                notification.reference_id,
                response.status_code,
            )
            raise

        return NotificationResponse.model_validate(response.json())


notifications_client = NotificationsClient()
