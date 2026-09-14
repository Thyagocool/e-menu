from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.infra.database import get_session
from src.modules.order.schemas import OrderCreate, OrderPreview, OrderRead
from src.modules.order.usecases import OrderService

router = APIRouter(prefix="/customers", tags=["orders"])


@router.post("/{customer_id}/checkout/preview", response_model=OrderPreview)
async def preview_checkout(customer_id: int, body: OrderCreate, session: AsyncSession = Depends(get_session)):
    service = OrderService()
    return await service.calculate(session, customer_id, body.delivery_type)


@router.post("/{customer_id}/checkout", response_model=OrderRead, status_code=201)
async def create_order(customer_id: int, body: OrderCreate, session: AsyncSession = Depends(get_session)):
    return await OrderService().create(session, customer_id, body)