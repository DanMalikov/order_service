from dependency_injector import containers, providers

from app.application.container import ApplicationContainer
from app.infrastructure.container import InfrastructureContainer


class AppContainer(containers.DeclarativeContainer):
    """Базовый контейнер"""

    config = providers.Configuration()

    infrastructure = providers.Container(
        InfrastructureContainer,
        config=config,
    )

    application = providers.Container(
        ApplicationContainer,
        infrastructure=infrastructure,
    )
