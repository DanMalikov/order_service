from app.config import settings
from app.container import AppContainer


def create_container() -> AppContainer:
    """Настройка контейнера с зависимостями проекта"""
    container = AppContainer()
    container.config.from_dict(settings.model_dump())
    container.wire(packages=["app.presentation"])
    return container
