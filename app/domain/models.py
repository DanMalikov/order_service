import enum
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class OrderStatus(str, enum.Enum):
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

