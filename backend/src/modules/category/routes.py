from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.infra.database import get_session, utcnow
from src.modules.category.models import Category
from src.modules.category.schemas import CategoryCreate, CategoryRead, CategoryUpdate
from src.modules.product.models import Product
from src.modules.restaurant.routes import get_or_404 as get_restaurant_or_404

router = APIRouter(tags=["categories"])


async def get_category_or_404(category_id: int, session: AsyncSession) -> Category:
    category = await session.get(Category, category_id)
    if category is None or category.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Categoria não encontrada")
    return category


@router.get("/restaurants/{restaurant_id}/categories", response_model=list[CategoryRead])
async def list_categories(
    restaurant_id: int, session: AsyncSession = Depends(get_session)
) -> list[Category]:
    await get_restaurant_or_404(restaurant_id, session)
    result = await session.scalars(
        select(Category)
        .where(Category.restaurant_id == restaurant_id, Category.deleted_at.is_(None))
        .order_by(Category.sort_order, Category.name)
    )
    return list(result)


@router.post("/restaurants/{restaurant_id}/categories", status_code=201, response_model=CategoryRead)
async def create_category(
    restaurant_id: int, payload: CategoryCreate, session: AsyncSession = Depends(get_session)
) -> Category:
    await get_restaurant_or_404(restaurant_id, session)
    category = Category(**payload.model_dump(), restaurant_id=restaurant_id)
    session.add(category)
    await session.commit()
    await session.refresh(category)
    return category


@router.put("/categories/{category_id}", response_model=CategoryRead)
async def update_category(
    category_id: int, payload: CategoryUpdate, session: AsyncSession = Depends(get_session)
) -> Category:
    category = await get_category_or_404(category_id, session)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(category, field, value)
    await session.commit()
    await session.refresh(category)
    return category


@router.delete("/categories/{category_id}", status_code=204)
async def delete_category(category_id: int, session: AsyncSession = Depends(get_session)) -> None:
    category = await get_category_or_404(category_id, session)
    has_products = await session.scalar(
        select(func.count()).select_from(Product).where(
            Product.category_id == category_id, Product.deleted_at.is_(None)
        )
    )
    if has_products:
        raise HTTPException(
            status_code=409,
            detail="Categoria possui produtos. Mova ou exclua os produtos antes.",
        )
    category.deleted_at = utcnow()
    await session.commit()