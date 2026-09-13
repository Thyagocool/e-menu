from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class RestaurantCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    slug: str | None = Field(default=None, max_length=120, pattern=r"^[a-z0-9-]+$")
    phone: str | None = Field(default=None, max_length=20)
    whatsapp_phone: str | None = Field(default=None, max_length=20)
    address: str | None = Field(default=None, max_length=255)
    opening_hours: str | None = Field(default=None, max_length=120)
    delivery_fee: Decimal = Field(default=Decimal("0"), ge=0)
    status: Literal["active", "inactive"] = "active"


class RestaurantUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    slug: str | None = Field(default=None, max_length=120, pattern=r"^[a-z0-9-]+$")
    phone: str | None = Field(default=None, max_length=20)
    whatsapp_phone: str | None = Field(default=None, max_length=20)
    address: str | None = Field(default=None, max_length=255)
    opening_hours: str | None = Field(default=None, max_length=120)
    delivery_fee: Decimal | None = Field(default=None, ge=0)
    status: Literal["active", "inactive"] | None = None


class RestaurantRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    slug: str
    phone: str | None
    whatsapp_phone: str | None
    address: str | None
    opening_hours: str | None
    delivery_fee: Decimal
    status: str
    created_at: datetime
    updated_at: datetime