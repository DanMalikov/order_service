from dependency_injector import containers, providers

from app.application.create_order_use_case import CreateOrderUseCase
from app.application.get_order_use_case import GetOrderUseCase
from app.application.payment_callback_use_case import PaymentCallbackUseCase


class ApplicationContainer(containers.DeclarativeContainer):
    """Контейнер с зависисомтями из application"""

    infrastructure = providers.DependenciesContainer()

    create_order_use_case = providers.Factory(
        CreateOrderUseCase,
        unit_of_work=infrastructure.unit_of_work,
    )

    get_order_use_case = providers.Factory(
        GetOrderUseCase,
        unit_of_work=infrastructure.unit_of_work,
    )

    payment_callback_use_case = providers.Factory(
        PaymentCallbackUseCase,
        unit_of_work=infrastructure.unit_of_work,
    )