from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel

from app.domain.models import OrderStatus, ShippingEventType


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


class CreateOutboxEventDTO(BaseModel):
    topic: str
    event_type: ShippingEventType
    payload: dict


class CreateInboxEventDTO(BaseModel):
    event_id: str
    event_type: ShippingEventType
    payload: dict


class ShippingEventDTO(BaseModel):
    event_type: ShippingEventType
    order_id: UUID
    item_id: UUID
    quantity: int
    shipment_id: UUID | None = None
    reason: str | None = None
    idempotency_key: str | None = None

    @property
    def inbox_event_id(self) -> str:
        return self.idempotency_key or f"{self.order_id}:{self.event_type.value}"
