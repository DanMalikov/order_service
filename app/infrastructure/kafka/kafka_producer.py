import json
import logging
from datetime import datetime
from uuid import UUID

from aiokafka import AIOKafkaProducer

logger = logging.getLogger(__name__)


def _json_serializer(value):
    def default(obj):
        if isinstance(obj, (datetime, UUID)):
            return str(obj)
        raise TypeError(f"Объект {type(obj).__name__} невозможно преобразовать")

    return json.dumps(value, default=default).encode("utf-8")


class KafkaProducerService:
    def __init__(self, bootstrap_servers: str):
        self._bootstrap_servers = bootstrap_servers
        self._producer: AIOKafkaProducer | None = None

    async def start(self) -> None:
        if self._producer is not None:
            return
        self._producer = AIOKafkaProducer(
            bootstrap_servers=self._bootstrap_servers,
            value_serializer=_json_serializer,
            acks="all",
            enable_idempotence=True,
        )
        await self._producer.start()

    async def stop(self) -> None:
        if self._producer is None:
            return
        await self._producer.stop()
        self._producer = None

    async def publish(self, topic: str, event: dict, key: str | None = None) -> None:
        if self._producer is None:
            raise RuntimeError("Kafka producer не запущен")
        try:
            await self._producer.send_and_wait(
                topic,
                value=event,
                key=key.encode("utf-8") if key else None,
            )
        except Exception:
            logger.exception(
                "Ошибка публикации kafka event: topic=%s, key=%s, order_id=%s",
                topic,
                key,
                event.get("order_id"),
            )
            raise
