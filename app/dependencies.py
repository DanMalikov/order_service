from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.clients import catalog_client
from app.database import get_db
from app.services import OrderService


async def get_order_service(session: AsyncSession = Depends(get_db)) -> OrderService:
    return OrderService(session=session, catalog_client=catalog_client)
