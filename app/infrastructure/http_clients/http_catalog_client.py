import logging
from datetime import datetime
from uuid import UUID

import httpx
from pydantic import BaseModel
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.exceptions import ItemNotFoundError

logger = logging.getLogger(__name__)


class CatalogItemResponse(BaseModel):
    id: UUID
    name: str
    price: str
    available_qty: int
    created_at: datetime


class CatalogClient:
    """Клиент для отправки запроса в сервис Catalog"""

    def __init__(self, base_url: str, api_key: str, timeout: float = 10.0) -> None:
        self._client = httpx.AsyncClient(
            base_url=base_url,
            headers={"X-API-Key": api_key},
            timeout=timeout,
        )

    @retry(
        stop=stop_after_attempt(4),
        wait=wait_exponential(multiplier=1, min=1, max=5),
        retry=retry_if_exception_type((httpx.RequestError, httpx.HTTPStatusError)),
        reraise=True,
    )
    async def get_item(self, item_id: UUID) -> CatalogItemResponse:
        url = f"/api/catalog/items/{item_id}"
        try:
            response = await self._client.get(url)

            logger.info(
                "Запрос предмета из Catalog. item_id=%s status_code=%s response_text=%s",
                str(item_id),
                response.status_code,
                response.text,
            )

        except httpx.RequestError:
            logger.exception(
                "Не удалось сделать Запрос из Catalog. item_id=%s url=%s",
                str(item_id),
                url,
            )
            raise

        if response.status_code == 404:
            raise ItemNotFoundError(f"Предмет {item_id} не найден")

        try:
            response.raise_for_status()
        except httpx.HTTPStatusError:
            logger.exception("Ошибка при работе с Catalog")
            raise

        return CatalogItemResponse.model_validate(response.json())
