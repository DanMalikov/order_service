import logging
from decimal import Decimal
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


class CreatePaymentRequest(BaseModel):
    order_id: UUID
    amount: Decimal
    callback_url: str
    idempotency_key: str


class PaymentResponse(BaseModel):
    id: UUID
    user_id: str
    order_id: UUID
    amount: Decimal
    status: str
    idempotency_key: str


class PaymentsClient:
    """Клиент для отправки запроса в сервис Payment"""

    def __init__(self) -> None:
        self._client = httpx.AsyncClient(
            base_url=settings.capashino_base_url,
            headers={"X-API-Key": settings.api_key},
            timeout=10.0,
        )

    @retry(
        stop=stop_after_attempt(4),
        wait=wait_exponential(multiplier=1, min=1, max=5),
        retry=retry_if_exception_type((httpx.RequestError, httpx.HTTPStatusError)),
        reraise=True,
    )
    async def create_payment(self, payment: CreatePaymentRequest) -> PaymentResponse:
        url = "/api/payments"
        payload = payment.model_dump(mode="json")

        logger.info(
            "Создаем платеж для Payments order_id=%s idempotency_key=%s callback_url=%s",
            str(payment.order_id),
            payment.idempotency_key,
            payment.callback_url,
        )

        try:
            response = await self._client.post(url, json=payload)
        except httpx.RequestError:
            logger.exception(
                "Не удалось сделать запрос в Payments. order_id=%s idempotency_key=%s",
                str(payment.order_id),
                payment.idempotency_key,
            )
            raise

        logger.info(
            "Ответ от Payments order_id=%s status_code=%s response_text=%s",
            str(payment.order_id),
            response.status_code,
            response.text,
        )

        try:
            response.raise_for_status()
        except httpx.HTTPStatusError:
            logger.exception("Ошибка при работе с Payments")
            raise

        return PaymentResponse.model_validate(response.json())


payments_client = PaymentsClient()
