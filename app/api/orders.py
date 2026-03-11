from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.dependencies import get_order_service
from app.exceptions import (
    CatalogServiceUnavailableError,
    ItemNotFoundError,
    NotEnoughQtyError,
    OrderNotFoundError,
)
from app.schemas import CreateOrderRequest, OrderResponse
from app.services import OrderService


router = APIRouter(prefix="/api/orders", tags=["orders"])


@router.post("", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    request_body: CreateOrderRequest,
    response: Response,
    service: OrderService = Depends(get_order_service),
) -> OrderResponse:
    try:
        order, created = await service.create_order(
            user_id=request_body.user_id,
            item_id=request_body.item_id,
            quantity=request_body.quantity,
            idempotency_key=request_body.idempotency_key,
        )
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

    if not created:
        response.status_code = status.HTTP_200_OK
    return OrderResponse.model_validate(order)


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: UUID, service: OrderService = Depends(get_order_service)
) -> OrderResponse:
    try:
        order = await service.get_order(order_id)
    except OrderNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    return OrderResponse.model_validate(order)
