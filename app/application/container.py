from dependency_injector import containers, providers

from app.application.use_cases.create_order_use_case import CreateOrderUseCase
from app.application.use_cases.get_order_use_case import GetOrderUseCase
from app.application.use_cases.payment_callback_use_case import PaymentCallbackUseCase
from app.application.use_cases.process_inbox_events_use_case import ProcessInboxEventsUseCase
from app.application.use_cases.process_outbox_events_use_case import ProcessOutboxEventsUseCase


class ApplicationContainer(containers.DeclarativeContainer):
    """Контейнер с зависисомтями из application"""

    infrastructure = providers.DependenciesContainer()
    config = providers.Configuration()

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

    process_outbox_events_use_case = providers.Factory(
        ProcessOutboxEventsUseCase,
        unit_of_work=infrastructure.unit_of_work,
        kafka_producer=infrastructure.kafka_producer,
        batch_size=config.outbox_batch_size,
        poll_interval=config.worker_poll_interval,
    )

    process_inbox_events_use_case = providers.Factory(
        ProcessInboxEventsUseCase,
        unit_of_work=infrastructure.unit_of_work,
        batch_size=config.inbox_batch_size,
        poll_interval=config.worker_poll_interval,
    )
