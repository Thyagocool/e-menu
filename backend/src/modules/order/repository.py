from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.order.models import Order


class OrderRepository:
    async def create(self, session: AsyncSession, order: Order) -> Order:
        session.add(order)
        await session.flush()
        return order

    async def get(self, session: AsyncSession, order_id: int) -> Order | None:
        return await session.get(Order, order_id)