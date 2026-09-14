from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.infra.database import Base, utcnow
from src.modules.whatsapp.models import Customer


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    restaurant_id: Mapped[int] = mapped_column(ForeignKey("restaurants.id"), index=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), index=True)
    status: Mapped[str] = mapped_column(String(20), default="RECEIVED")
    delivery_type: Mapped[str] = mapped_column(String(20), default="retirada")
    address: Mapped[str | None] = mapped_column(String(300))
    payment_method: Mapped[str] = mapped_column(String(20), default="pix")
    delivery_fee: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0"))
    subtotal: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    total: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    items: Mapped[list["OrderItem"]] = relationship(
        back_populates="order", cascade="all, delete-orphan", lazy="selectin"
    )
    customer: Mapped[Customer] = relationship()


class OrderItem(Base):
    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), index=True)
    product_id: Mapped[int | None] = mapped_column(ForeignKey("products.id"))
    product_name: Mapped[str] = mapped_column(String(150))
    variant_name: Mapped[str | None] = mapped_column(String(100))
    unit_price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    quantity: Mapped[int] = mapped_column(Integer)
    line_total: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    # snapshot dos adicionais em JSON: [{"name": "...", "price": "..."}]
    addons: Mapped[str | None] = mapped_column(Text)

    order: Mapped[Order] = relationship(back_populates="items")