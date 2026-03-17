from datetime import datetime
from uuid import UUID

from app.domain.models import OrderStatus

from pydantic import BaseModel

class CreateOrderDTO(BaseModel):
    user_id: str
    quantity: int
    item_id: UUID
    idempotency_key: str

class OrderDTO(BaseModel):
    id: UUID
    user_id: str
    quantity: int
    item_id: UUID
    status: OrderStatus
    created_at: datetime
    updated_at: datetime