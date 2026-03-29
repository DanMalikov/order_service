import json
import logging

from aiokafka import AIOKafkaConsumer

from app.application.dto import CreateInboxEventDTO, ShippingEventDTO
from app.exceptions import DuplicateInboxEventError, InvalidShippingEventError
from app.infrastructure.uow import UnitOfWork

logger = logging.getLogger(__name__)


class KafkaConsumerService:
    def __init__(
        self,
        bootstrap_servers: str,
        topic: str,
        group_id: str,
        unit_of_work: UnitOfWork,
    ):
        self._bootstrap_servers = bootstrap_servers
        self._topic = topic
        self._group_id = group_id
        self._unit_of_work = unit_of_work
        self._consumer: AIOKafkaConsumer | None = None
        self._is_running = False

    async def start(self) -> None:
        if self._consumer is not None:
            return
        self._consumer = AIOKafkaConsumer(
            self._topic,
            bootstrap_servers=self._bootstrap_servers,
            group_id=self._group_id,
            enable_auto_commit=False,
            auto_offset_reset="earliest",
            value_deserializer=lambda m: json.loads(m.decode("utf-8")) if m else None,
        )
        await self._consumer.start()
        self._is_running = True

    async def stop(self) -> None:
        self._is_running = False
        if self._consumer is None:
            return
        await self._consumer.stop()
        self._consumer = None

    async def run(self) -> None:
        await self.start()
        assert self._consumer is not None
        logger.info(
            "Kafka consumer запущен topic=%s group_id=%s", self._topic, self._group_id
        )

        try:
            async for message in self._consumer:
                if not self._is_running:
                    break
                payload = message.value
                if payload is None:
                    await self._consumer.commit()
                    continue

                logger.info("Consumer принял сообщение. payload = %s", payload)

                try:
                    event = ShippingEventDTO.model_validate(payload)

                    async with self._unit_of_work() as uow:
                        await uow.inbox.create(
                            CreateInboxEventDTO(
                                event_id=event.inbox_event_id,
                                event_type=event.event_type,
                                payload=event.model_dump(mode="json"),
                            )
                        )
                        await uow.commit()
                        logger.info("Сообщение с заказом %s передано в Inbox", event.order_id)


                    await self._consumer.commit()
                except DuplicateInboxEventError:
                    logger.info("В inbox пропущен дубликат event=%s", event)
                    await self._consumer.commit()
                except (ValueError, InvalidShippingEventError):
                    logger.exception("Invalid kafka event payload=%s", payload)
                    await self._consumer.commit()
                    continue
                except Exception:
                    logger.exception(
                        "Ошибка при сохранении kafka event в inbox. payload=%s", payload
                    )
                    continue
        finally:
            await self.stop()
