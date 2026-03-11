from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.models import OrderStatus


class CreateOrderRequest(BaseModel):
    user_id: str
    quantity: int = Field(gt=0)
    item_id: UUID
    idempotency_key: str


class OrderResponse(BaseModel):
    id: UUID
    user_id: str
    quantity: int
    item_id: UUID
    status: OrderStatus
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CatalogItemResponse(BaseModel):
    id: UUID
    name: str
    price: str
    available_qty: int
    created_at: datetime
