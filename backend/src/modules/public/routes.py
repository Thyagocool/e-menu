from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.infra.database import get_session
from src.modules.public.schemas import MenuRead, ProductPublicRead
from src.modules.public.usecases import PublicMenuUseCases

router = APIRouter(prefix="/public", tags=["public"])
usecases = PublicMenuUseCases()


@router.get("/restaurants/{slug}/menu", response_model=MenuRead)
async def get_menu(slug: str, session: AsyncSession = Depends(get_session)) -> dict:
    return await usecases.get_menu(session, slug)


@router.get("/restaurants/{slug}/products/{product_id}", response_model=ProductPublicRead)
async def get_product(slug: str, product_id: int, session: AsyncSession = Depends(get_session)) -> dict:
    return await usecases.get_product(session, slug, product_id)