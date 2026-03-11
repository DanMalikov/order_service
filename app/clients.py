import httpx
from uuid import UUID

from app.config import settings
from app.exceptions import CatalogServiceUnavailableError, ItemNotFoundError
from app.schemas import CatalogItemResponse

import logging

logger = logging.getLogger(__name__)


class CatalogClient:
    def __init__(self) -> None:
        self._client = httpx.AsyncClient(
            base_url=settings.capashino_base_url,
            headers={"X-API-Key": settings.api_key},
            timeout=10.0,
        )

    async def get_item(self, item_id: UUID) -> CatalogItemResponse:
        url = f"/api/catalog/items/{item_id}"
        logger.info("Запрашиваемый предмет", extra={"item_id": str(item_id), "url": url})
        try:
            response = await self._client.get(url)

            logger.info(
                "Запрос предмета из Catalog",
                extra={
                    "item_id": str(item_id),
                    "status_code": response.status_code,
                    "response_text": response.text,
                },
            )

        except httpx.RequestError as exc:

            logger.exception(
                "Запрос из Catalog сломался",
                extra={
                    "item_id": str(item_id),
                    "url": url,
                },
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

        try:
            return CatalogItemResponse.model_validate(response.json())
        except Exception as exc:
            raise CatalogServiceUnavailableError(
                "Данные из Catalog не прошли валидацию"
            ) from exc


catalog_client = CatalogClient()
