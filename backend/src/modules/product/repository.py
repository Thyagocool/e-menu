from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.product.models import Addon, Product, ProductVariant


class ProductRepository:
    async def get(self, session: AsyncSession, product_id: int) -> Product | None:
        return await session.get(Product, product_id)

    async def list_by_restaurant(self, session: AsyncSession, restaurant_id: int) -> list[Product]:
        result = await session.scalars(
            select(Product)
            .where(Product.restaurant_id == restaurant_id, Product.deleted_at.is_(None))
            .order_by(Product.name)
        )
        return list(result)

    async def get_variant(self, session: AsyncSession, variant_id: int) -> ProductVariant | None:
        return await session.get(ProductVariant, variant_id)

    async def get_addon(self, session: AsyncSession, addon_id: int) -> Addon | None:
        return await session.get(Addon, addon_id)

    async def list_addons_by_restaurant(self, session: AsyncSession, restaurant_id: int) -> list[Addon]:
        result = await session.scalars(
            select(Addon).where(Addon.restaurant_id == restaurant_id).order_by(Addon.name)
        )
        return list(result)