from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from dependency_injector.wiring import Provide, inject

from app.application.create_order_use_case import CreateOrderUseCase
from app.application.dto import CreateOrderDTO, OrderDTO, PaymentCallbackDTO
from app.application.get_order_use_case import GetOrderUseCase
from app.application.payment_callback_use_case import PaymentCallbackUseCase
from app.container import AppContainer
from app.exceptions import (
    CatalogServiceUnavailableError,
    ItemNotFoundError,
    NotEnoughQtyError,
    OrderNotFoundError,
)

router_order = APIRouter(prefix="/api/orders", tags=["orders"])


class CreateOrderRequest(CreateOrderDTO):
    pass


class OrderResponse(OrderDTO):
    pass


class PaymentCallbackRequest(PaymentCallbackDTO):
    pass


@router_order.post(
    "", response_model=OrderResponse, status_code=status.HTTP_201_CREATED
)
@inject
async def create_order(
    order: CreateOrderRequest,
    create_order_use_case: CreateOrderUseCase = Depends(Provide[AppContainer.application.create_order_use_case]),
) -> OrderResponse:

    try:
        result = await create_order_use_case(new_order=order)
    except ItemNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc
    except NotEnoughQtyError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc
    except CatalogServiceUnavailableError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)
        ) from exc

    return result


@router_order.get("/{order_id}", response_model=OrderResponse)
@inject
async def get_order(
    order_id: UUID, order_use_case: GetOrderUseCase = Depends(Provide[AppContainer.application.get_order_use_case])
):
    try:
        result = await order_use_case(order_id)
    except OrderNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return result


@router_order.post("/payment-callback", status_code=status.HTTP_200_OK)
async def payment_callback(
    callback: PaymentCallbackRequest,
    process_payment_callback_use_case: PaymentCallbackUseCase = Depends(
        Provide[AppContainer.application.payment_callback_use_case]
    ),
) -> Response:
    try:
        await process_payment_callback_use_case(callback=callback)
    except OrderNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return Response(status_code=status.HTTP_200_OK)
