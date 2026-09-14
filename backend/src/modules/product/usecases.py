from sqlalchemy.ext.asyncio import AsyncSession

from src.infra.database import utcnow
from src.infra.errors import DomainError
from src.modules.category.models import Category
from src.modules.product.models import Addon, Product, ProductVariant
from src.modules.product.repository import ProductRepository
from src.modules.product.schemas import (
    AddonCreate,
    ProductCreate,
    ProductUpdate,
    VariantCreate,
)
from src.modules.restaurant.usecases import RestaurantUseCases


class ProductUseCases:
    def __init__(
        self,
        repository: ProductRepository | None = None,
        restaurants: RestaurantUseCases | None = None,
    ):
        self.repository = repository or ProductRepository()
        self.restaurants = restaurants or RestaurantUseCases()

    async def _get_active(self, session: AsyncSession, product_id: int) -> Product:
        product = await self.repository.get(session, product_id)
        if product is None or product.deleted_at is not None:
            raise DomainError(404, "Produto não encontrado")
        return product

    async def _ensure_category_owned(
        self, session: AsyncSession, category_id: int | None, restaurant_id: int
    ) -> None:
        if category_id is None:
            return
        category = await session.get(Category, category_id)
        if category is None or category.restaurant_id != restaurant_id or category.deleted_at is not None:
            raise DomainError(400, "Categoria inválida para este restaurante")

    async def _get_addon_owned(self, session: AsyncSession, addon_id: int, restaurant_id: int) -> Addon:
        addon = await self.repository.get_addon(session, addon_id)
        if addon is None or addon.restaurant_id != restaurant_id:
            raise DomainError(400, "Adicional inválido para este restaurante")
        return addon

    async def list_products(self, session: AsyncSession, restaurant_id: int) -> list[Product]:
        await self.restaurants.get(session, restaurant_id)
        return await self.repository.list_by_restaurant(session, restaurant_id)

    async def create(self, session: AsyncSession, restaurant_id: int, payload: ProductCreate) -> Product:
        await self.restaurants.get(session, restaurant_id)
        await self._ensure_category_owned(session, payload.category_id, restaurant_id)
        product = Product(**payload.model_dump(), restaurant_id=restaurant_id)
        session.add(product)
        await session.commit()
        await session.refresh(product)
        return product

    async def get(self, session: AsyncSession, product_id: int) -> Product:
        return await self._get_active(session, product_id)

    async def update(self, session: AsyncSession, product_id: int, payload: ProductUpdate) -> Product:
        product = await self._get_active(session, product_id)
        data = payload.model_dump(exclude_unset=True)
        if data.get("category_id") is not None:
            await self._ensure_category_owned(session, data["category_id"], product.restaurant_id)
        for field, value in data.items():
            setattr(product, field, value)
        await session.commit()
        await session.refresh(product)
        return product

    async def delete(self, session: AsyncSession, product_id: int) -> None:
        product = await self._get_active(session, product_id)
        product.deleted_at = utcnow()
        await session.commit()

    async def create_variant(
        self, session: AsyncSession, product_id: int, payload: VariantCreate
    ) -> ProductVariant:
        product = await self._get_active(session, product_id)
        variant = ProductVariant(**payload.model_dump(), product_id=product.id)
        session.add(variant)
        await session.commit()
        await session.refresh(variant)
        return variant

    async def update_variant(
        self, session: AsyncSession, variant_id: int, payload: VariantCreate
    ) -> ProductVariant:
        variant = await self.repository.get_variant(session, variant_id)
        if variant is None:
            raise DomainError(404, "Variação não encontrada")
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(variant, field, value)
        await session.commit()
        await session.refresh(variant)
        return variant

    async def delete_variant(self, session: AsyncSession, variant_id: int) -> None:
        variant = await self.repository.get_variant(session, variant_id)
        if variant is None:
            raise DomainError(404, "Variação não encontrada")
        await session.delete(variant)
        await session.commit()

    async def list_addons(self, session: AsyncSession, restaurant_id: int) -> list[Addon]:
        await self.restaurants.get(session, restaurant_id)
        return await self.repository.list_addons_by_restaurant(session, restaurant_id)

    async def create_addon(self, session: AsyncSession, restaurant_id: int, payload: AddonCreate) -> Addon:
        await self.restaurants.get(session, restaurant_id)
        addon = Addon(**payload.model_dump(), restaurant_id=restaurant_id)
        session.add(addon)
        await session.commit()
        await session.refresh(addon)
        return addon

    async def update_addon(self, session: AsyncSession, addon_id: int, payload: AddonCreate) -> Addon:
        addon = await self.repository.get_addon(session, addon_id)
        if addon is None:
            raise DomainError(404, "Adicional não encontrado")
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(addon, field, value)
        await session.commit()
        await session.refresh(addon)
        return addon

    async def delete_addon(self, session: AsyncSession, addon_id: int) -> None:
        addon = await self.repository.get_addon(session, addon_id)
        if addon is None:
            raise DomainError(404, "Adicional não encontrado")
        addon.status = "inactive"
        await session.commit()

    async def attach_addon(self, session: AsyncSession, product_id: int, addon_id: int) -> Addon:
        product = await self._get_active(session, product_id)
        addon = await self._get_addon_owned(session, addon_id, product.restaurant_id)
        if addon not in product.addons:
            product.addons.append(addon)
            await session.commit()
        return addon

    async def detach_addon(self, session: AsyncSession, product_id: int, addon_id: int) -> None:
        product = await self._get_active(session, product_id)
        addon = next((a for a in product.addons if a.id == addon_id), None)
        if addon is None:
            raise DomainError(404, "Adicional não vinculado a este produto")
        product.addons.remove(addon)
        await session.commit()