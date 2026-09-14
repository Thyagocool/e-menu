import json
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from src.infra.errors import DomainError
from src.modules.cart.usecases import CartService
from src.modules.order.models import Order, OrderItem
from src.modules.order.repository import OrderRepository
from src.modules.order.schemas import (
    ORDER_STATUSES,
    DashboardRead,
    OrderCreate,
    OrderItemRead,
    OrderPreview,
    OrderRead,
    TopProduct,
)
from src.modules.restaurant.repository import RestaurantRepository
from src.modules.whatsapp.repository import CustomerRepository

DELIVERY_TYPES = {"retirada", "entrega"}
PAYMENT_METHODS = {"pix", "dinheiro", "cartao"}


class OrderService:
    def __init__(
        self,
        carts: CartService | None = None,
        orders: OrderRepository | None = None,
        restaurants: RestaurantRepository | None = None,
        customers: CustomerRepository | None = None,
    ):
        self.carts = carts or CartService()
        self.orders = orders or OrderRepository()
        self.restaurants = restaurants or RestaurantRepository()
        self.customers = customers or CustomerRepository()

    async def calculate(
        self, session: AsyncSession, customer_id: int, delivery_type: str = "retirada"
    ) -> OrderPreview:
        if delivery_type not in DELIVERY_TYPES:
            raise DomainError(400, "Tipo de entrega inválido (use retirada ou entrega)")
        cart = await self.carts.get_cart(session, customer_id)
        if not cart.items:
            raise DomainError(400, "Carrinho vazio")
        if delivery_type == "entrega":
            fee = await self._delivery_fee(session, customer_id)
        else:
            fee = Decimal("0.00")
        subtotal = cart.subtotal
        return OrderPreview(
            delivery_type=delivery_type,
            subtotal=subtotal,
            delivery_fee=fee,
            total=subtotal + fee,
            items=[self._item_read(i) for i in cart.items],
        )

    async def create(
        self, session: AsyncSession, customer_id: int, data: OrderCreate
    ) -> OrderRead:
        if not data.confirmed:  # US-026: confirmação explícita antes de criar
            raise DomainError(400, "Confirme o pedido para finalizar")
        customer = await self.customers.get(session, customer_id)
        if customer is None:
            raise DomainError(404, "Cliente não encontrado")
        cart = await self.carts.get_cart(session, customer_id)
        if not cart.items:
            raise DomainError(400, "Carrinho vazio")
        if data.delivery_type == "entrega" and not (data.address and data.address.strip()):
            raise DomainError(400, "Informe o endereço para entrega (US-028)")
        await self._revalidate_products(session, cart.items)

        subtotal = cart.subtotal
        fee = (
            (await self.restaurants.get(session, customer.restaurant_id)).delivery_fee
            if data.delivery_type == "entrega"
            else Decimal("0.00")
        )
        order = Order(
            restaurant_id=customer.restaurant_id,
            customer_id=customer_id,
            delivery_type=data.delivery_type,
            address=data.address.strip() if data.address else None,
            payment_method=data.payment_method,
            delivery_fee=fee,
            subtotal=subtotal,
            total=subtotal + fee,
        )
        for item in cart.items:
            order.items.append(OrderItem(
                product_id=item.product_id,
                product_name=item.product_name,
                variant_name=item.variant_name,
                unit_price=item.unit_price,
                quantity=item.quantity,
                line_total=item.line_total,
                addons=json.dumps(
                    [{"name": a.name, "price": str(a.price)} for a in item.addons],
                    ensure_ascii=False,
                )
                if item.addons
                else None,
            ))
        await self.orders.create(session, order)
        await session.commit()
        result = self._read(order)  # dump antes do clear (clear expira a sessão)
        # snapshot travado; carrinho vira o que for pedido de novo
        await self.carts.clear(session, customer_id)
        return result

    async def list_by_restaurant(
        self, session: AsyncSession, restaurant_id: int, status: str | None = None
    ) -> list[OrderRead]:
        orders = await self.orders.list_by_restaurant(session, restaurant_id, status)
        return [self._read(o) for o in orders]

    async def get(self, session: AsyncSession, order_id: int) -> OrderRead:
        order = await self.orders.get(session, order_id)
        if order is None:
            raise DomainError(404, "Pedido não encontrado")
        return self._read(order)

    async def update_status(self, session: AsyncSession, order_id: int, status: str) -> OrderRead:
        if status not in ORDER_STATUSES:
            raise DomainError(400, f"Status inválido: {status}")
        order = await self.orders.get(session, order_id)
        if order is None:
            raise DomainError(404, "Pedido não encontrado")
        order.status = status
        await session.commit()
        # expira a relação customer (commit não expira colunas; reload garante nome fresco)
        await session.refresh(order, attribute_names=["customer"])
        return self._read(order)

    async def dashboard(self, session: AsyncSession, restaurant_id: int) -> DashboardRead:
        if await self.restaurants.get(session, restaurant_id) is None:
            raise DomainError(404, "Restaurante não encontrado")
        data = await self.orders.dashboard(session, restaurant_id)
        return DashboardRead(
            orders_today=data["orders_today"],
            revenue_today=data["revenue_today"],
            pending_orders=data["pending_orders"],
            top_products=[TopProduct(**p) for p in data["top_products"]],
        )

    async def _delivery_fee(self, session: AsyncSession, customer_id: int) -> Decimal:
        customer = await self.customers.get(session, customer_id)
        if customer is None:
            raise DomainError(404, "Cliente não encontrado")
        restaurant = await self.restaurants.get(session, customer.restaurant_id)
        # sessão pode estar expirada (cart clear); fee é valor do restaurante
        return restaurant.delivery_fee

    async def _revalidate_products(self, session: AsyncSession, items) -> None:
        # garantia: produto inativo/removido não pode ser vendido (preço vem do snapshot do carrinho)
        from src.modules.product.repository import ProductRepository

        products = ProductRepository()
        for item in items:
            product = await products.get(session, item.product_id)
            if product is None or product.status != "active" or product.deleted_at is not None:
                raise DomainError(409, f"Produto indisponível: {item.product_name}")

    def _item_read(self, item) -> OrderItemRead:
        return OrderItemRead(
            product_name=item.product_name,
            variant_name=item.variant_name,
            unit_price=item.unit_price,
            quantity=item.quantity,
            line_total=item.line_total,
            addons=json.loads(item.addons) if item.addons else [],
        )

    def _read(self, order: Order) -> OrderRead:
        return OrderRead(
            id=order.id,
            status=order.status,
            delivery_type=order.delivery_type,
            address=order.address,
            payment_method=order.payment_method,
            delivery_fee=order.delivery_fee,
            subtotal=order.subtotal,
            total=order.total,
            customer_name=order.customer.name if order.customer else None,
            created_at=order.created_at,
            items=[self._item_read(i) for i in order.items],
        )