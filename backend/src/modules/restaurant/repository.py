from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.restaurant.models import Restaurant


class RestaurantRepository:
    async def get(self, session: AsyncSession, restaurant_id: int) -> Restaurant | None:
        return await session.get(Restaurant, restaurant_id)

    async def get_by_slug(
        self, session: AsyncSession, slug: str, exclude_id: int | None = None
    ) -> Restaurant | None:
        query = select(Restaurant).where(Restaurant.slug == slug)
        if exclude_id is not None:
            query = query.where(Restaurant.id != exclude_id)
        return await session.scalar(query)