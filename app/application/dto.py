from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel

from app.domain.models import OrderStatus


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


class PaymentCallbackStatus(StrEnum):
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class PaymentCallbackDTO(BaseModel):
    payment_id: UUID
    order_id: UUID
    status: PaymentCallbackStatus
    amount: Decimal
    error_message: str | None = None
