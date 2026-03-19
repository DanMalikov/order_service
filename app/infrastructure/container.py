from dependency_injector import containers, providers
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.infrastructure.uow import UnitOfWork


class InfrastructureContainer(containers.DeclarativeContainer):
    """Контейнер с зависимостями из infrastructure"""

    config = providers.Configuration()

    engine = providers.Singleton[AsyncEngine](
        create_async_engine, config.get_db_string, echo=False, future=True
    )

    session_factory = providers.Factory(
        async_sessionmaker, bind=engine, class_=AsyncSession, expire_on_commit=False
    )

    unit_of_work = providers.Factory(UnitOfWork, session_factory)
