from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field

ORDER_STATUSES = ("RECEIVED", "CONFIRMED", "PREPARING", "READY", "DELIVERING", "COMPLETED", "CANCELLED")


class OrderCreate(BaseModel):
    delivery_type: Literal["retirada", "entrega"] = "retirada"
    address: str | None = Field(default=None, max_length=300)
    payment_method: Literal["pix", "dinheiro", "cartao"] = "pix"
    confirmed: bool = True  # garantia US-026: pedido só nasce com confirmação


class StatusUpdate(BaseModel):
    status: Literal["RECEIVED", "CONFIRMED", "PREPARING", "READY", "DELIVERING", "COMPLETED", "CANCELLED"]


class OrderItemRead(BaseModel):
    product_name: str
    variant_name: str | None = None
    unit_price: Decimal
    quantity: int
    line_total: Decimal
    addons: list[dict] = Field(default_factory=list)


class OrderRead(BaseModel):
    id: int
    status: str
    delivery_type: str
    address: str | None = None
    payment_method: str
    delivery_fee: Decimal
    subtotal: Decimal
    total: Decimal
    customer_name: str | None = None
    created_at: datetime | None = None
    items: list[OrderItemRead]


class OrderPreview(BaseModel):
    delivery_type: Literal["retirada", "entrega"] = "retirada"
    subtotal: Decimal
    delivery_fee: Decimal
    total: Decimal
    items: list[OrderItemRead]


class TopProduct(BaseModel):
    name: str
    quantity: int
    revenue: Decimal


class DashboardRead(BaseModel):
    orders_today: int
    revenue_today: Decimal
    pending_orders: int
    top_products: list[TopProduct]