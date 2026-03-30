from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel


class ShippingEventType(StrEnum):
    ORDER_PAID = "order.paid"
    ORDER_SHIPPED = "order.shipped"
    ORDER_CANCELLED = "order.cancelled"


class OutboxEventStatus(StrEnum):
    PENDING = "PENDING"
    SENT = "SENT"


class InboxEventStatus(StrEnum):
    PENDING = "PENDING"
    PROCESSED = "PROCESSED"


class OrderStatus(StrEnum):
    NEW = "NEW"
    PAID = "PAID"
    SHIPPED = "SHIPPED"
    CANCELLED = "CANCELLED"


class Order(BaseModel):
    id: UUID
    user_id: str
    quantity: int
    item_id: UUID
    status: OrderStatus
    created_at: datetime
    updated_at: datetime


class Item(BaseModel):
    id: UUID
    name: str
    price: str
    available_qty: int
    created_at: datetime


class OutboxEvent(BaseModel):
    id: UUID
    topic: str
    event_type: ShippingEventType
    payload: dict
    status: OutboxEventStatus
    created_at: datetime
    updated_at: datetime


class InboxEvent(BaseModel):
    id: UUID
    event_id: str
    event_type: ShippingEventType
    payload: dict
    status: InboxEventStatus
    created_at: datetime
    processed_at: datetime | None = None
