from sqlalchemy.ext.asyncio import AsyncSession

from src.infra.errors import DomainError
from src.modules.category.repository import CategoryRepository
from src.modules.product.models import Addon, Product, ProductVariant
from src.modules.product.repository import ProductRepository
from src.modules.restaurant.models import Restaurant
from src.modules.restaurant.repository import RestaurantRepository


def _active_variants(product: Product) -> list[ProductVariant]:
    return [v for v in product.variants if v.status == "active"]


def _active_addons(product: Product) -> list[Addon]:
    return [a for a in product.addons if a.status == "active"]


def _product_public(product: Product) -> dict:
    return {
        "id": product.id,
        "name": product.name,
        "description": product.description,
        "image_url": product.image_url,
        "base_price": product.base_price,
        "variants": _active_variants(product),
        "addons": _active_addons(product),
    }


class PublicMenuUseCases:
    def __init__(
        self,
        restaurants: RestaurantRepository | None = None,
        categories: CategoryRepository | None = None,
        products: ProductRepository | None = None,
    ):
        self.restaurants = restaurants or RestaurantRepository()
        self.categories = categories or CategoryRepository()
        self.products = products or ProductRepository()

    async def _get_active_restaurant(self, session: AsyncSession, slug: str) -> Restaurant:
        restaurant = await self.restaurants.get_by_slug(session, slug)
        if restaurant is None or restaurant.status != "active":
            raise DomainError(404, "Cardápio não encontrado")
        return restaurant

    async def get_menu(self, session: AsyncSession, slug: str) -> dict:
        restaurant = await self._get_active_restaurant(session, slug)
        categories = [
            c
            for c in await self.categories.list_by_restaurant(session, restaurant.id)
            if c.status == "active"
        ]
        products = [
            p for p in await self.products.list_by_restaurant(session, restaurant.id) if p.status == "active"
        ]
        by_category: dict[int | None, list[Product]] = {}
        for product in products:
            by_category.setdefault(product.category_id, []).append(product)
        return {
            "restaurant": restaurant,
            "categories": [
                {
                    "id": c.id,
                    "name": c.name,
                    "products": [_product_public(p) for p in by_category.get(c.id, [])],
                }
                for c in categories
            ],
            "uncategorized_products": [_product_public(p) for p in by_category.get(None, [])],
        }

    async def get_product(self, session: AsyncSession, slug: str, product_id: int) -> Product:
        restaurant = await self._get_active_restaurant(session, slug)
        product = await self.products.get(session, product_id)
        if (
            product is None
            or product.deleted_at is not None
            or product.status != "active"
            or product.restaurant_id != restaurant.id
        ):
            raise DomainError(404, "Produto não encontrado")
        return _product_public(product)