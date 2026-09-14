from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.modules.order.models import Order


class OrderRepository:
    async def create(self, session: AsyncSession, order: Order) -> Order:
        session.add(order)
        await session.flush()
        return order

    async def get(self, session: AsyncSession, order_id: int) -> Order | None:
        stmt = select(Order).where(Order.id == order_id).options(selectinload(Order.customer))
        return (await session.scalars(stmt)).first()

    async def list_by_restaurant(
        self, session: AsyncSession, restaurant_id: int, status: str | None = None
    ) -> list[Order]:
        stmt = (
            select(Order)
            .where(Order.restaurant_id == restaurant_id)
            .options(selectinload(Order.customer))
            .order_by(Order.id.desc())
        )
        if status:
            stmt = stmt.where(Order.status == status)
        return list((await session.scalars(stmt)).all())