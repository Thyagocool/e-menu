from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.category.models import Category


class CategoryRepository:
    async def get(self, session: AsyncSession, category_id: int) -> Category | None:
        return await session.get(Category, category_id)

    async def list_by_restaurant(self, session: AsyncSession, restaurant_id: int) -> list[Category]:
        result = await session.scalars(
            select(Category)
            .where(Category.restaurant_id == restaurant_id, Category.deleted_at.is_(None))
            .order_by(Category.sort_order, Category.name)
        )
        return list(result)