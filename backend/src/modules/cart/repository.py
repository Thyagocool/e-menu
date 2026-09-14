from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.cart.models import Cart


class CartRepository:
    async def get_by_customer(self, session: AsyncSession, customer_id: int) -> Cart | None:
        return await session.scalar(
            select(Cart).where(Cart.customer_id == customer_id)
        )

    async def create(self, session: AsyncSession, customer_id: int) -> Cart:
        cart = Cart(customer_id=customer_id)
        session.add(cart)
        return cart