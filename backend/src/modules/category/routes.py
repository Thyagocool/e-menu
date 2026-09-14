from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.infra.database import get_session
from src.modules.category.models import Category
from src.modules.category.schemas import CategoryCreate, CategoryRead, CategoryUpdate
from src.modules.category.usecases import CategoryUseCases

router = APIRouter(tags=["categories"])
usecases = CategoryUseCases()


@router.get("/restaurants/{restaurant_id}/categories", response_model=list[CategoryRead])
async def list_categories(restaurant_id: int, session: AsyncSession = Depends(get_session)) -> list[Category]:
    return await usecases.list_categories(session, restaurant_id)


@router.post("/restaurants/{restaurant_id}/categories", status_code=201, response_model=CategoryRead)
async def create_category(
    restaurant_id: int, payload: CategoryCreate, session: AsyncSession = Depends(get_session)
) -> Category:
    return await usecases.create(session, restaurant_id, payload)


@router.put("/categories/{category_id}", response_model=CategoryRead)
async def update_category(
    category_id: int, payload: CategoryUpdate, session: AsyncSession = Depends(get_session)
) -> Category:
    return await usecases.update(session, category_id, payload)


@router.delete("/categories/{category_id}", status_code=204)
async def delete_category(category_id: int, session: AsyncSession = Depends(get_session)) -> None:
    await usecases.delete(session, category_id)