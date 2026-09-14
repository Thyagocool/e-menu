from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.infra.database import get_session
from src.modules.order.schemas import DashboardRead, OrderCreate, OrderPreview, OrderRead, StatusUpdate
from src.modules.order.usecases import OrderService

router = APIRouter(prefix="/customers", tags=["orders"])
admin_router = APIRouter(tags=["orders"])


@router.post("/{customer_id}/checkout/preview", response_model=OrderPreview)
async def preview_checkout(customer_id: int, body: OrderCreate, session: AsyncSession = Depends(get_session)):
    service = OrderService()
    return await service.calculate(session, customer_id, body.delivery_type)


@router.post("/{customer_id}/checkout", response_model=OrderRead, status_code=201)
async def create_order(customer_id: int, body: OrderCreate, session: AsyncSession = Depends(get_session)):
    return await OrderService().create(session, customer_id, body)


@admin_router.get("/restaurants/{restaurant_id}/orders", response_model=list[OrderRead])
async def list_orders(
    restaurant_id: int,
    status: str | None = None,
    session: AsyncSession = Depends(get_session),
):
    return await OrderService().list_by_restaurant(session, restaurant_id, status)


@admin_router.get("/orders/{order_id}", response_model=OrderRead)
async def get_order(order_id: int, session: AsyncSession = Depends(get_session)):
    return await OrderService().get(session, order_id)


@admin_router.put("/orders/{order_id}/status", response_model=OrderRead)
async def update_order_status(
    order_id: int, body: StatusUpdate, session: AsyncSession = Depends(get_session)
):
    return await OrderService().update_status(session, order_id, body.status)


@admin_router.get("/restaurants/{restaurant_id}/dashboard", response_model=DashboardRead)
async def restaurant_dashboard(restaurant_id: int, session: AsyncSession = Depends(get_session)):
    return await OrderService().dashboard(session, restaurant_id)