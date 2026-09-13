import re
import unicodedata

from sqlalchemy.ext.asyncio import AsyncSession

from src.infra.errors import DomainError
from src.modules.restaurant.models import Restaurant
from src.modules.restaurant.repository import RestaurantRepository
from src.modules.restaurant.schemas import RestaurantCreate, RestaurantUpdate


def slugify(name: str) -> str:
    normalized = unicodedata.normalize("NFKD", name)
    ascii_name = normalized.encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", ascii_name.lower()).strip("-")


class RestaurantUseCases:
    def __init__(self, repository: RestaurantRepository | None = None):
        self.repository = repository or RestaurantRepository()

    async def get(self, session: AsyncSession, restaurant_id: int) -> Restaurant:
        restaurant = await self.repository.get(session, restaurant_id)
        if restaurant is None:
            raise DomainError(404, "Restaurante não encontrado")
        return restaurant

    async def create(self, session: AsyncSession, payload: RestaurantCreate) -> Restaurant:
        slug = payload.slug or slugify(payload.name)
        if await self.repository.get_by_slug(session, slug):
            raise DomainError(409, "Slug já em uso")
        restaurant = Restaurant(**payload.model_dump(exclude={"slug"}), slug=slug)
        session.add(restaurant)
        await session.commit()
        await session.refresh(restaurant)
        return restaurant

    async def update(
        self, session: AsyncSession, restaurant_id: int, payload: RestaurantUpdate
    ) -> Restaurant:
        restaurant = await self.get(session, restaurant_id)
        data = payload.model_dump(exclude_unset=True)
        if "slug" in data and data["slug"] is not None:
            if await self.repository.get_by_slug(session, data["slug"], exclude_id=restaurant_id):
                raise DomainError(409, "Slug já em uso")
        for field, value in data.items():
            setattr(restaurant, field, value)
        await session.commit()
        await session.refresh(restaurant)
        return restaurant