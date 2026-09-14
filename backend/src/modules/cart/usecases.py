from decimal import Decimal

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.infra.errors import DomainError
from src.modules.cart.models import Cart, CartItem, CartItemAddon
from src.modules.cart.repository import CartRepository
from src.modules.cart.schemas import CartRead
from src.modules.product.repository import ProductRepository
from src.modules.whatsapp.repository import CustomerRepository

MAX_QUANTITY = 99

_CART_LOADS = (
    selectinload(Cart.customer),
    selectinload(Cart.items).selectinload(CartItem.product),
    selectinload(Cart.items).selectinload(CartItem.variant),
    selectinload(Cart.items).selectinload(CartItem.addons).selectinload(CartItemAddon.addon),
)


class CartService:
    def __init__(
        self,
        carts: CartRepository | None = None,
        products: ProductRepository | None = None,
        customers: CustomerRepository | None = None,
    ):
        self.carts = carts or CartRepository()
        self.products = products or ProductRepository()
        self.customers = customers or CustomerRepository()

    async def get_cart(self, session: AsyncSession, customer_id: int) -> CartRead:
        await self._customer(session, customer_id)
        cart = await self._fresh_cart(session, customer_id)
        if cart is None:
            cart = self._create_cart(session, customer_id)
            await session.flush()  # atribui o id para o CartRead
        return self._read(session, cart)

    async def add_item(
        self,
        session: AsyncSession,
        customer_id: int,
        product_id: int,
        variant_id: int | None,
        quantity: int,
        addon_ids: list[int],
    ) -> CartRead:
        customer = await self._customer(session, customer_id)
        cart = await self._get_cart(session, customer_id)
        restaurant_id = customer.restaurant_id

        product = await self.products.get(session, product_id)
        if (
            product is None
            or product.deleted_at is not None
            or product.status != "active"
            or product.restaurant_id != restaurant_id
        ):
            raise DomainError(400, "Produto indisponível")

        active_variants = [v for v in product.variants if v.status == "active"]
        if active_variants:
            if variant_id is None:
                raise DomainError(400, "Selecione uma variação")
            variant = next((v for v in active_variants if v.id == variant_id), None)
            if variant is None:
                raise DomainError(400, "Variação inválida para este produto")
            unit_price = variant.price
        else:
            if variant_id is not None:
                raise DomainError(400, "Este produto não possui variações")
            unit_price = product.base_price

        addons = []
        for addon_id in dict.fromkeys(addon_ids):  # dedup preservando ordem
            addon = await self.products.get_addon(session, addon_id)
            if (
                addon is None
                or addon.restaurant_id != restaurant_id
                or addon.status != "active"
                or addon not in product.addons
            ):
                raise DomainError(400, "Adicional inválido para este produto")
            addons.append(addon)

        # mesmo produto + variação + mesmos adicionais => soma quantidade
        key = sorted(addon.id for addon in addons)
        for item in cart.items:
            if (
                item.product_id == product_id
                and item.variant_id == variant_id
                and sorted(a.addon_id for a in item.addons) == key
            ):
                item.quantity = min(item.quantity + quantity, MAX_QUANTITY)
                return await self._commit_and_read(session, customer_id)

        item = CartItem(
            cart_id=cart.id,
            product_id=product_id,
            variant_id=variant_id,
            quantity=quantity,
            unit_price=unit_price,
        )
        session.add(item)
        await session.flush()
        for addon in addons:
            session.add(CartItemAddon(cart_item_id=item.id, addon_id=addon.id, price=addon.price))
        return await self._commit_and_read(session, customer_id)

    async def update_quantity(
        self, session: AsyncSession, item_id: int, quantity: int
    ) -> CartRead:
        cart = await self._item_cart(session, item_id)
        item = next(i for i in cart.items if i.id == item_id)
        item.quantity = quantity
        return await self._commit_and_read(session, cart.customer_id)

    async def remove_item(self, session: AsyncSession, item_id: int) -> CartRead:
        cart = await self._item_cart(session, item_id)
        item = next(i for i in cart.items if i.id == item_id)
        await session.delete(item)
        return await self._commit_and_read(session, cart.customer_id)

    async def clear(self, session: AsyncSession, customer_id: int) -> CartRead:
        cart = await self._get_cart(session, customer_id)
        item_ids = [item.id for item in cart.items]
        if item_ids:
            await session.execute(delete(CartItemAddon).where(CartItemAddon.cart_item_id.in_(item_ids)))
            await session.execute(delete(CartItem).where(CartItem.id.in_(item_ids)))
        return await self._commit_and_read(session, customer_id)

    async def _customer(self, session: AsyncSession, customer_id: int):
        customer = await self.customers.get(session, customer_id)
        if customer is None:
            raise DomainError(404, "Cliente não encontrado")
        return customer

    async def _get_cart(self, session: AsyncSession, customer_id: int) -> Cart:
        cart = await self._fresh_cart(session, customer_id)
        if cart is None:
            cart = self._create_cart(session, customer_id)
        return cart

    def _create_cart(self, session: AsyncSession, customer_id: int) -> Cart:
        cart = Cart(customer_id=customer_id)
        # autoflush de session.get() tornaria a collection vazia "unloaded"
        # e a iteração dispararia IO síncrona (MissingGreenlet); atribuir
        # inicializa como carregada sem query
        cart.items = []
        session.add(cart)
        return cart

    async def _fresh_cart(self, session: AsyncSession, customer_id: int) -> Cart | None:
        return await session.scalar(
            select(Cart).options(*_CART_LOADS).where(Cart.customer_id == customer_id)
        )

    async def _item_cart(self, session: AsyncSession, item_id: int) -> Cart:
        cart = await session.scalar(
            select(Cart).join(CartItem).options(*_CART_LOADS).where(CartItem.id == item_id)
        )
        if cart is None:
            raise DomainError(404, "Item não encontrado")
        return cart

    async def _commit_and_read(self, session: AsyncSession, customer_id: int) -> CartRead:
        await session.commit()
        session.expire_all()
        cart = await self._fresh_cart(session, customer_id)
        return self._read(session, cart)

    def _read(self, session: AsyncSession, cart: Cart) -> CartRead:
        items = []
        for item in cart.items:
            addon_total = sum(a.price for a in item.addons)
            items.append(
                {
                    "id": item.id,
                    "product_id": item.product_id,
                    "product_name": item.product.name,
                    "variant_id": item.variant_id,
                    "variant_name": item.variant.name if item.variant else None,
                    "quantity": item.quantity,
                    "unit_price": item.unit_price,
                    "addons": [
                        {"addon_id": a.addon_id, "name": a.addon.name, "price": a.price}
                        for a in item.addons
                    ],
                    "line_total": (item.unit_price + addon_total) * item.quantity,
                }
            )
        subtotal = sum((i["line_total"] for i in items), Decimal("0.00"))
        return CartRead(id=cart.id, customer_id=cart.customer_id, items=items, subtotal=subtotal)