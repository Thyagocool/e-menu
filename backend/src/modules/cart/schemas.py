from decimal import Decimal

from pydantic import BaseModel, Field


class CartItemCreate(BaseModel):
    customer_id: int
    product_id: int
    variant_id: int | None = None
    quantity: int = Field(ge=1, le=99)
    addon_ids: list[int] = Field(default_factory=list)


class CartItemUpdate(BaseModel):
    quantity: int = Field(ge=1, le=99)


class CartItemAddonRead(BaseModel):
    addon_id: int
    name: str
    price: Decimal


class CartItemRead(BaseModel):
    id: int
    product_id: int
    product_name: str
    variant_id: int | None
    variant_name: str | None
    quantity: int
    unit_price: Decimal
    addons: list[CartItemAddonRead]
    line_total: Decimal


class CartRead(BaseModel):
    id: int
    customer_id: int
    items: list[CartItemRead]
    subtotal: Decimal