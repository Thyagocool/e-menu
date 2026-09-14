from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.infra.database import Base, utcnow

if TYPE_CHECKING:
    from src.modules.product.models import Addon, Product, ProductVariant
    from src.modules.whatsapp.models import Customer


class Cart(Base):
    __tablename__ = "carts"

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    customer: Mapped["Customer"] = relationship(lazy="selectin")
    items: Mapped[list["CartItem"]] = relationship(
        back_populates="cart", cascade="all, delete-orphan", lazy="selectin"
    )


class CartItem(Base):
    __tablename__ = "cart_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    cart_id: Mapped[int] = mapped_column(ForeignKey("carts.id"), index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    variant_id: Mapped[int | None] = mapped_column(ForeignKey("product_variants.id"))
    quantity: Mapped[int] = mapped_column(Integer)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    cart: Mapped[Cart] = relationship(back_populates="items", lazy="selectin")
    product: Mapped["Product"] = relationship(lazy="selectin")
    variant: Mapped["ProductVariant | None"] = relationship(lazy="selectin")
    addons: Mapped[list["CartItemAddon"]] = relationship(
        back_populates="cart_item", cascade="all, delete-orphan", lazy="selectin"
    )


class CartItemAddon(Base):
    __tablename__ = "cart_item_addons"

    cart_item_id: Mapped[int] = mapped_column(ForeignKey("cart_items.id"), primary_key=True)
    addon_id: Mapped[int] = mapped_column(ForeignKey("addons.id"), primary_key=True)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2))

    cart_item: Mapped[CartItem] = relationship(back_populates="addons", lazy="selectin")
    addon: Mapped["Addon"] = relationship(lazy="selectin")