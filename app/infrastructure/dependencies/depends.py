from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.application.create_order import CreateOrderUseCase
from app.application.get_order import GetOrderUseCase
from app.application.payment_callback import ProcessPaymentCallbackUseCase
from app.infrastructure.dependencies.db import session_factory
from app.infrastructure.uow import UnitOfWork


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    return session_factory


def get_unit_of_work(
    session_factory: async_sessionmaker[AsyncSession] = Depends(get_session_factory),
) -> UnitOfWork:
    return UnitOfWork(session_factory=session_factory)


def get_create_order_use_case(
    uow: UnitOfWork = Depends(get_unit_of_work),
) -> CreateOrderUseCase:
    return CreateOrderUseCase(unit_of_work=uow)


def get_order_use_case(
    uow: UnitOfWork = Depends(get_unit_of_work),
) -> GetOrderUseCase:
    return GetOrderUseCase(unit_of_work=uow)


def get_process_payment_callback_use_case(
    uow: UnitOfWork = Depends(get_unit_of_work),
) -> ProcessPaymentCallbackUseCase:
    return ProcessPaymentCallbackUseCase(unit_of_work=uow)
