from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.cart.usecases import CartService
from src.modules.product.models import Product
from src.modules.product.repository import ProductRepository
from src.modules.restaurant.repository import RestaurantRepository


def _schema(name: str, description: str, properties: dict, required: list[str]) -> dict:
    return {
        "name": name,
        "description": description,
        "parameters": {"type": "object", "properties": properties, "required": required},
    }


def _summary_product(product: Product) -> dict:
    variants = [
        {"id": v.id, "name": v.name, "price": str(v.price)}
        for v in product.variants
        if v.status == "active"
    ]
    addons = [
        {"id": a.id, "name": a.name, "price": str(a.price)}
        for a in product.addons
        if a.status == "active"
    ]
    return {
        "id": product.id,
        "name": product.name,
        "description": product.description,
        "base_price": str(product.base_price),
        "variants": variants,
        "addons": addons,
    }


class ToolRegistry:
    def __init__(
        self,
        restaurants: RestaurantRepository | None = None,
        products: ProductRepository | None = None,
        carts: CartService | None = None,
    ):
        self.restaurants = restaurants or RestaurantRepository()
        self.products = products or ProductRepository()
        self.carts = carts or CartService()
        self._tools: dict[str, dict] = {}
        self._register_all()

    def _register(self, fn) -> None:
        self._tools[fn.__name__] = {"handler": fn, "schema": fn.schema}  # type: ignore[attr-defined]

    def list_schemas(self) -> list[dict]:
        return [t["schema"] for t in self._tools.values()]

    async def execute(self, session: AsyncSession, name: str, **kwargs) -> dict:
        tool = self._tools.get(name)
        if tool is None:
            return {"error": f"Ferramenta desconhecida: {name}"}
        try:
            return await tool["handler"](session, **kwargs)
        except Exception as exc:  # noqa: BLE001 - erro da tool vira mensagem amigável
            return {"error": str(exc)}

    # --- tools -----------------------------------------------------------

    async def get_restaurant_info(self, session: AsyncSession, restaurant_id: int) -> dict:
        restaurant = await self.restaurants.get(session, restaurant_id)
        if restaurant is None:
            return {"error": "Restaurante não encontrado"}
        lines = [
            f"*{restaurant.name}*",
            restaurant.description or "",
            f"📍 {restaurant.address}" if restaurant.address else "",
            f"🕐 {restaurant.opening_hours}" if restaurant.opening_hours else "",
            f"Entrega: {restaurant.delivery_fee}" if restaurant.delivery_fee else "",
        ]
        return {
            "name": restaurant.name,
            "description": restaurant.description,
            "address": restaurant.address,
            "opening_hours": restaurant.opening_hours,
            "delivery_fee": str(restaurant.delivery_fee),
            "resumo": "\n".join(line for line in lines if line),
        }
    get_restaurant_info.schema = _schema(  # type: ignore[attr-defined]
        "get_restaurant_info",
        "Informações gerais do restaurante (endereço, horário, taxa de entrega, descrição).",
        {"restaurant_id": {"type": "integer"}},
        ["restaurant_id"],
    )

    async def search_products(self, session: AsyncSession, restaurant_id: int, query: str = "") -> dict:
        term = query.strip().lower()
        singular = term[:-1] if term.endswith("s") else term
        result = await session.scalars(
            select(Product).where(
                Product.restaurant_id == restaurant_id,
                Product.status == "active",
                Product.deleted_at.is_(None),
            )
        )
        products = [
            p for p in result
            if not term
            or term in p.name.lower()
            or singular in p.name.lower()
            or (p.description and (term in p.description.lower() or singular in p.description.lower()))
        ]
        products.sort(key=lambda p: (0 if p.name.lower().startswith(term) else 1, p.name.lower()))
        return {"products": [_summary_product(p) for p in products[:10]]}
    search_products.schema = _schema(  # type: ignore[attr-defined]
        "search_products",
        "Busca produtos no cardápio por nome ou descrição. Query vazia lista tudo.",
        {"restaurant_id": {"type": "integer"}, "query": {"type": "string"}},
        ["restaurant_id"],
    )

    async def get_product(self, session: AsyncSession, product_id: int) -> dict:
        product = await self.products.get(session, product_id)
        if product is None or product.status != "active" or product.deleted_at is not None:
            return {"error": "Produto não encontrado"}
        return _summary_product(product)
    get_product.schema = _schema(  # type: ignore[attr-defined]
        "get_product",
        "Detalhe de um produto com variações e adicionais.",
        {"product_id": {"type": "integer"}},
        ["product_id"],
    )

    async def get_cart(self, session: AsyncSession, customer_id: int) -> dict:
        return (await self.carts.get_cart(session, customer_id)).model_dump()
    get_cart.schema = _schema(  # type: ignore[attr-defined]
        "get_cart",
        "Retorna o carrinho atual do cliente com itens e subtotal.",
        {"customer_id": {"type": "integer"}},
        ["customer_id"],
    )

    async def add_to_cart(
        self,
        session: AsyncSession,
        customer_id: int,
        product_id: int,
        quantity: int = 1,
        variant_id: int | None = None,
        addon_ids: list[int] | None = None,
    ) -> dict:
        return (
            await self.carts.add_item(
                session, customer_id, product_id, variant_id, quantity, addon_ids or []
            )
        ).model_dump()
    add_to_cart.schema = _schema(  # type: ignore[attr-defined]
        "add_to_cart",
        "Adiciona um produto ao carrinho do cliente. Use product_id retornado por search_products.",
        {
            "customer_id": {"type": "integer"},
            "product_id": {"type": "integer"},
            "quantity": {"type": "integer"},
            "variant_id": {"type": ["integer", "null"]},
            "addon_ids": {"type": "array", "items": {"type": "integer"}},
        },
        ["customer_id", "product_id"],
    )

    async def update_cart_item(
        self, session: AsyncSession, customer_id: int, item_id: int, quantity: int
    ) -> dict:
        return (await self.carts.update_quantity(session, item_id, quantity)).model_dump()
    update_cart_item.schema = _schema(  # type: ignore[attr-defined]
        "update_cart_item",
        "Altera a quantidade de um item existente no carrinho.",
        {
            "customer_id": {"type": "integer"},
            "item_id": {"type": "integer"},
            "quantity": {"type": "integer"},
        },
        ["customer_id", "item_id", "quantity"],
    )

    async def remove_cart_item(self, session: AsyncSession, customer_id: int, item_id: int) -> dict:
        return (await self.carts.remove_item(session, item_id)).model_dump()
    remove_cart_item.schema = _schema(  # type: ignore[attr-defined]
        "remove_cart_item",
        "Remove um item do carrinho do cliente.",
        {"customer_id": {"type": "integer"}, "item_id": {"type": "integer"}},
        ["customer_id", "item_id"],
    )

    def _register_all(self) -> None:
        for name in (
            "get_restaurant_info",
            "search_products",
            "get_product",
            "get_cart",
            "add_to_cart",
            "update_cart_item",
            "remove_cart_item",
        ):
            self._register(getattr(self, name))