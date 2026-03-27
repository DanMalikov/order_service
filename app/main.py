import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.presentation.router_order import router_order
from app.utils.create_container import create_container
from app.utils.logger import configure_logging

configure_logging()
container = create_container()


@asynccontextmanager
async def lifespan(_: FastAPI):
    kafka_producer = container.infrastructure.kafka_producer()
    kafka_consumer = container.infrastructure.kafka_consumer()
    outbox_worker = container.application.process_outbox_events_use_case()
    inbox_worker = container.application.process_inbox_events_use_case()

    await kafka_producer.start()

    outbox_task = asyncio.create_task(outbox_worker.run())
    inbox_task = asyncio.create_task(inbox_worker.run())
    consumer_task = asyncio.create_task(kafka_consumer.run())

    try:
        yield
    finally:
        outbox_worker.stop()
        inbox_worker.stop()
        await kafka_consumer.stop()
        await asyncio.gather(
            outbox_task, inbox_task, consumer_task, return_exceptions=True
        )
        await kafka_producer.stop()


app = FastAPI()
app.container = container
app.include_router(router_order)


@app.get("/")
async def healthcheck() -> dict[str, str]:
    return {"status": "ok"}
