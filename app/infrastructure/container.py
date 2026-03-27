from dependency_injector import containers, providers
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.infrastructure.kafka.kafka_consumer import KafkaConsumerService
from app.infrastructure.kafka.kafka_producer import KafkaProducerService
from app.infrastructure.uow import UnitOfWork


class InfrastructureContainer(containers.DeclarativeContainer):
    """Контейнер с зависимостями из infrastructure"""

    config = providers.Configuration()

    engine = providers.Singleton[AsyncEngine](
        create_async_engine,
        config.get_db_string,
        echo=False,
        future=True,
        pool_pre_ping=True,
    )

    session_factory = providers.Singleton(
        async_sessionmaker, bind=engine, class_=AsyncSession, expire_on_commit=False
    )

    unit_of_work = providers.Factory(UnitOfWork, session_factory)

    kafka_producer = providers.Singleton(
        KafkaProducerService,
        bootstrap_servers=config.kafka_bootstrap_servers,
    )

    kafka_consumer = providers.Singleton(
        KafkaConsumerService,
        bootstrap_servers=config.kafka_bootstrap_servers,
        topic=config.kafka_shipment_events_topic,
        group_id=config.kafka_consumer_group_id,
        unit_of_work=unit_of_work,
    )
