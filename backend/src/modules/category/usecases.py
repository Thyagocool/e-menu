from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.infra.database import utcnow
from src.infra.errors import DomainError
from src.modules.category.models import Category
from src.modules.category.repository import CategoryRepository
from src.modules.category.schemas import CategoryCreate, CategoryUpdate
from src.modules.product.models import Product
from src.modules.restaurant.usecases import RestaurantUseCases


class CategoryUseCases:
    def __init__(
        self,
        repository: CategoryRepository | None = None,
        restaurants: RestaurantUseCases | None = None,
    ):
        self.repository = repository or CategoryRepository()
        self.restaurants = restaurants or RestaurantUseCases()

    async def _get_active(self, session: AsyncSession, category_id: int) -> Category:
        category = await self.repository.get(session, category_id)
        if category is None or category.deleted_at is not None:
            raise DomainError(404, "Categoria não encontrada")
        return category

    async def list_categories(self, session: AsyncSession, restaurant_id: int) -> list[Category]:
        await self.restaurants.get(session, restaurant_id)
        return await self.repository.list_by_restaurant(session, restaurant_id)

    async def create(self, session: AsyncSession, restaurant_id: int, payload: CategoryCreate) -> Category:
        await self.restaurants.get(session, restaurant_id)
        category = Category(**payload.model_dump(), restaurant_id=restaurant_id)
        session.add(category)
        await session.commit()
        await session.refresh(category)
        return category

    async def update(self, session: AsyncSession, category_id: int, payload: CategoryUpdate) -> Category:
        category = await self._get_active(session, category_id)
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(category, field, value)
        await session.commit()
        await session.refresh(category)
        return category

    async def delete(self, session: AsyncSession, category_id: int) -> None:
        category = await self._get_active(session, category_id)
        has_products = await session.scalar(
            select(func.count()).select_from(Product).where(
                Product.category_id == category_id, Product.deleted_at.is_(None)
            )
        )
        if has_products:
            raise DomainError(
                409, "Categoria possui produtos. Mova ou exclua os produtos antes."
            )
        category.deleted_at = utcnow()
        await session.commit()