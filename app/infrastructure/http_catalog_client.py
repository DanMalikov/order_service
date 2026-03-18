import logging
from datetime import datetime
from uuid import UUID

import httpx
from pydantic import BaseModel

from app.config import settings
from app.exceptions import CatalogServiceUnavailableError, ItemNotFoundError

logger = logging.getLogger(__name__)


class CatalogItemResponse(BaseModel):
    id: UUID
    name: str
    price: str
    available_qty: int
    created_at: datetime


class CatalogClient:
    """Клиент для отправки запроса в сервис Catalog"""
    def __init__(self) -> None:
        self._client = httpx.AsyncClient(
            base_url=settings.capashino_base_url,
            headers={"X-API-Key": settings.api_key},
            timeout=10.0,
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

        except httpx.RequestError as exc:
            logger.exception(
                "Запрос из Catalog сломался. item_id=%s url=%s", str(item_id), url
            )

            raise CatalogServiceUnavailableError(
                "Не удалось получить предмет из сервиса Catalog"
            ) from exc

        if response.status_code == 404:
            raise ItemNotFoundError(f"Предмет {item_id} не найден")

        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise CatalogServiceUnavailableError("Ошибка при работе с Catalog") from exc

        return CatalogItemResponse.model_validate(response.json())


catalog_client = CatalogClient()
