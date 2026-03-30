import asyncio
import logging

from app.infrastructure.kafka.kafka_producer import KafkaProducerService
from app.infrastructure.uow import UnitOfWork

logger = logging.getLogger(__name__)


class ProcessOutboxEventsUseCase:
    """Реализация паттерна Outbox"""

    def __init__(
        self,
        unit_of_work: UnitOfWork,
        kafka_producer: KafkaProducerService,
        batch_size: int = 100,
        poll_interval: float = 5.0,
    ):
        self._unit_of_work = unit_of_work
        self._kafka_producer = kafka_producer
        self._batch_size = batch_size
        self._poll_interval = poll_interval
        self._is_running = False

    def stop(self) -> None:
        self._is_running = False

    async def process_batch(self) -> int:
        processed = 0
        async with self._unit_of_work() as uow:
            events = await uow.outbox.get_pending_events_for_update(
                limit=self._batch_size
            )
            if not events:
                logger.info("events для Outbox не найдено. Уходим на ожидание")
                return 0

            logger.info("Количество найденных events для Outbox = %s", len(events))

            for event in events:
                await self._kafka_producer.publish(
                    topic=event.topic,
                    event=event.payload,
                    key=str(event.id),
                )
                logger.info(
                    "Публикуем событие в Kafka: topic=%s key=%s payload=%s",
                    event.topic,
                    event.id,
                    event.payload,
                )

                await uow.outbox.mark_as_sent(event.id)

                logger.info(
                    "Объект отправлен в kafka. order_id=%s", event.payload["order_id"]
                )
                processed += 1

            await uow.commit()
        return processed

    async def run(self) -> None:
        self._is_running = True
        logger.info("Outbox worker запущен")
        while self._is_running:
            try:
                processed = await self.process_batch()
                if processed == 0:
                    await asyncio.sleep(self._poll_interval)
            except Exception:
                logger.exception("Outbox worker упал в цикле")
                await asyncio.sleep(self._poll_interval)
