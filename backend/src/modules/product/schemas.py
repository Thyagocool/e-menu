from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ProductCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    category_id: int | None = None
    description: str | None = Field(default=None, max_length=500)
    image_url: str | None = Field(default=None, max_length=255)
    base_price: Decimal = Field(ge=0)
    status: Literal["active", "inactive"] = "active"


class ProductUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    category_id: int | None = None
    description: str | None = Field(default=None, max_length=500)
    image_url: str | None = Field(default=None, max_length=255)
    base_price: Decimal | None = Field(default=None, ge=0)
    status: Literal["active", "inactive"] | None = None


class VariantCreate(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    price: Decimal = Field(ge=0)
    status: Literal["active", "inactive"] = "active"


class VariantRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    price: Decimal
    status: str


class AddonCreate(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    price: Decimal = Field(ge=0, default=Decimal("0"))


class AddonRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    restaurant_id: int
    name: str
    price: Decimal
    status: str


class ProductRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    restaurant_id: int
    category_id: int | None
    name: str
    description: str | None
    image_url: str | None
    base_price: Decimal
    status: str
    created_at: datetime
    updated_at: datetime


class ProductDetailRead(ProductRead):
    variants: list[VariantRead] = []
    addons: list[AddonRead] = []