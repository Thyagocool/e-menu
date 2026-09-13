from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.infra.database import get_session
from src.modules.restaurant.models import Restaurant
from src.modules.restaurant.schemas import RestaurantCreate, RestaurantRead, RestaurantUpdate
from src.modules.restaurant.usecases import RestaurantUseCases

router = APIRouter(prefix="/restaurants", tags=["restaurants"])
usecases = RestaurantUseCases()


@router.post("", status_code=201, response_model=RestaurantRead)
async def create_restaurant(
    payload: RestaurantCreate, session: AsyncSession = Depends(get_session)
) -> Restaurant:
    return await usecases.create(session, payload)


@router.get("/{restaurant_id}", response_model=RestaurantRead)
async def get_restaurant(restaurant_id: int, session: AsyncSession = Depends(get_session)) -> Restaurant:
    return await usecases.get(session, restaurant_id)


@router.put("/{restaurant_id}", response_model=RestaurantRead)
async def update_restaurant(
    restaurant_id: int, payload: RestaurantUpdate, session: AsyncSession = Depends(get_session)
) -> Restaurant:
    return await usecases.update(session, restaurant_id, payload)