from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class RestaurantPublicRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    slug: str
    name: str
    phone: str | None
    whatsapp_phone: str | None
    address: str | None
    opening_hours: str | None
    delivery_fee: Decimal


class VariantPublicRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    price: Decimal


class AddonPublicRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    price: Decimal


class ProductPublicRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None
    image_url: str | None
    base_price: Decimal
    variants: list[VariantPublicRead] = []
    addons: list[AddonPublicRead] = []


class CategoryPublicRead(BaseModel):
    id: int
    name: str
    products: list[ProductPublicRead]


class MenuRead(BaseModel):
    restaurant: RestaurantPublicRead
    categories: list[CategoryPublicRead]
    uncategorized_products: list[ProductPublicRead] = []