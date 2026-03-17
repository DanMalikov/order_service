import logging
from uuid import UUID

from fastapi import APIRouter, status, Depends, HTTPException

from app.application.create_order import CreateOrderUseCase
from app.application.dto import CreateOrderDTO, OrderDTO
from app.application.get_order import GetOrderUseCase

from app.exceptions import ItemNotFoundError, NotEnoughQtyError, CatalogServiceUnavailableError, OrderNotFoundError
from app.infrastructure.dependencies.depends import get_create_order_use_case, get_order_use_case
logger = logging.getLogger(__name__)
router_order = APIRouter(prefix="/api/orders", tags=["orders"])

class CreateOrderRequest(CreateOrderDTO):
    pass

class OrderResponse(OrderDTO):
    pass


@router_order.post("", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    order: CreateOrderRequest,
    create_order_use_case: CreateOrderUseCase = Depends(get_create_order_use_case),
) -> OrderResponse:
    logging.info("а тут уже не начало")
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
async def get_order(order_id: UUID, order_use_case: GetOrderUseCase = Depends(get_order_use_case)):
    try:
        result = await order_use_case(order_id)
    except OrderNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return result

