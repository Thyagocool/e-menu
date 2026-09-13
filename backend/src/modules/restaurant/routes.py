import re
import unicodedata

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.infra.database import get_session
from src.modules.restaurant.models import Restaurant
from src.modules.restaurant.schemas import RestaurantCreate, RestaurantRead, RestaurantUpdate

router = APIRouter(prefix="/restaurants", tags=["restaurants"])


def slugify(name: str) -> str:
    normalized = unicodedata.normalize("NFKD", name)
    ascii_name = normalized.encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", ascii_name.lower()).strip("-")


async def get_or_404(restaurant_id: int, session: AsyncSession) -> Restaurant:
    restaurant = await session.get(Restaurant, restaurant_id)
    if restaurant is None:
        raise HTTPException(status_code=404, detail="Restaurante não encontrado")
    return restaurant


@router.post("", status_code=201, response_model=RestaurantRead)
async def create_restaurant(
    payload: RestaurantCreate, session: AsyncSession = Depends(get_session)
) -> Restaurant:
    slug = payload.slug or slugify(payload.name)
    existing = await session.scalar(select(Restaurant).where(Restaurant.slug == slug))
    if existing:
        raise HTTPException(status_code=409, detail="Slug já em uso")
    restaurant = Restaurant(**payload.model_dump(exclude={"slug"}), slug=slug)
    session.add(restaurant)
    await session.commit()
    await session.refresh(restaurant)
    return restaurant


@router.get("/{restaurant_id}", response_model=RestaurantRead)
async def get_restaurant(restaurant_id: int, session: AsyncSession = Depends(get_session)) -> Restaurant:
    return await get_or_404(restaurant_id, session)


@router.put("/{restaurant_id}", response_model=RestaurantRead)
async def update_restaurant(
    restaurant_id: int, payload: RestaurantUpdate, session: AsyncSession = Depends(get_session)
) -> Restaurant:
    restaurant = await get_or_404(restaurant_id, session)
    data = payload.model_dump(exclude_unset=True)
    if "slug" in data and data["slug"] is not None:
        existing = await session.scalar(
            select(Restaurant).where(Restaurant.slug == data["slug"], Restaurant.id != restaurant_id)
        )
        if existing:
            raise HTTPException(status_code=409, detail="Slug já em uso")
    for field, value in data.items():
        setattr(restaurant, field, value)
    await session.commit()
    await session.refresh(restaurant)
    return restaurant