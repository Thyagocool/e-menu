from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.infra.database import get_session
from src.modules.product.models import Addon, Product, ProductVariant
from src.modules.product.schemas import (
    AddonCreate,
    AddonRead,
    ProductCreate,
    ProductDetailRead,
    ProductRead,
    ProductUpdate,
    VariantCreate,
    VariantRead,
)
from src.modules.product.usecases import ProductUseCases

router = APIRouter(tags=["products"])
usecases = ProductUseCases()


@router.get("/restaurants/{restaurant_id}/products", response_model=list[ProductRead])
async def list_products(restaurant_id: int, session: AsyncSession = Depends(get_session)) -> list[Product]:
    return await usecases.list_products(session, restaurant_id)


@router.post("/restaurants/{restaurant_id}/products", status_code=201, response_model=ProductRead)
async def create_product(
    restaurant_id: int, payload: ProductCreate, session: AsyncSession = Depends(get_session)
) -> Product:
    return await usecases.create(session, restaurant_id, payload)


@router.get("/products/{product_id}", response_model=ProductDetailRead)
async def get_product(product_id: int, session: AsyncSession = Depends(get_session)) -> Product:
    return await usecases.get(session, product_id)


@router.put("/products/{product_id}", response_model=ProductRead)
async def update_product(
    product_id: int, payload: ProductUpdate, session: AsyncSession = Depends(get_session)
) -> Product:
    return await usecases.update(session, product_id, payload)


@router.delete("/products/{product_id}", status_code=204)
async def delete_product(product_id: int, session: AsyncSession = Depends(get_session)) -> None:
    await usecases.delete(session, product_id)


@router.post("/products/{product_id}/variants", status_code=201, response_model=VariantRead)
async def create_variant(
    product_id: int, payload: VariantCreate, session: AsyncSession = Depends(get_session)
) -> ProductVariant:
    return await usecases.create_variant(session, product_id, payload)


@router.put("/variants/{variant_id}", response_model=VariantRead)
async def update_variant(
    variant_id: int, payload: VariantCreate, session: AsyncSession = Depends(get_session)
) -> ProductVariant:
    return await usecases.update_variant(session, variant_id, payload)


@router.delete("/variants/{variant_id}", status_code=204)
async def delete_variant(variant_id: int, session: AsyncSession = Depends(get_session)) -> None:
    await usecases.delete_variant(session, variant_id)


@router.get("/restaurants/{restaurant_id}/addons", response_model=list[AddonRead])
async def list_addons(restaurant_id: int, session: AsyncSession = Depends(get_session)) -> list[Addon]:
    return await usecases.list_addons(session, restaurant_id)


@router.post("/restaurants/{restaurant_id}/addons", status_code=201, response_model=AddonRead)
async def create_addon(
    restaurant_id: int, payload: AddonCreate, session: AsyncSession = Depends(get_session)
) -> Addon:
    return await usecases.create_addon(session, restaurant_id, payload)


@router.put("/addons/{addon_id}", response_model=AddonRead)
async def update_addon(
    addon_id: int, payload: AddonCreate, session: AsyncSession = Depends(get_session)
) -> Addon:
    return await usecases.update_addon(session, addon_id, payload)


@router.delete("/addons/{addon_id}", status_code=204)
async def delete_addon(addon_id: int, session: AsyncSession = Depends(get_session)) -> None:
    await usecases.delete_addon(session, addon_id)


@router.post("/products/{product_id}/addons", status_code=201, response_model=AddonRead)
async def attach_addon(product_id: int, payload: dict, session: AsyncSession = Depends(get_session)) -> Addon:
    return await usecases.attach_addon(session, product_id, payload["addon_id"])


@router.delete("/products/{product_id}/addons/{addon_id}", status_code=204)
async def detach_addon(product_id: int, addon_id: int, session: AsyncSession = Depends(get_session)) -> None:
    await usecases.detach_addon(session, product_id, addon_id)