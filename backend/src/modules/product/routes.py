from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.infra.database import get_session, utcnow
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
from src.modules.restaurant.routes import get_or_404 as get_restaurant_or_404

router = APIRouter(tags=["products"])


async def get_product_or_404(product_id: int, session: AsyncSession) -> Product:
    product = await session.get(Product, product_id)
    if product is None or product.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    return product


async def ensure_category_owned(category_id: int | None, restaurant_id: int, session: AsyncSession) -> None:
    if category_id is None:
        return
    from src.modules.category.models import Category

    category = await session.get(Category, category_id)
    if category is None or category.restaurant_id != restaurant_id or category.deleted_at is not None:
        raise HTTPException(status_code=400, detail="Categoria inválida para este restaurante")


def apply_product_data(product: Product, data: dict) -> None:
    for field, value in data.items():
        setattr(product, field, value)


@router.get("/restaurants/{restaurant_id}/products", response_model=list[ProductRead])
async def list_products(restaurant_id: int, session: AsyncSession = Depends(get_session)) -> list[Product]:
    await get_restaurant_or_404(restaurant_id, session)
    result = await session.scalars(
        select(Product)
        .where(Product.restaurant_id == restaurant_id, Product.deleted_at.is_(None))
        .order_by(Product.name)
    )
    return list(result)


@router.post("/restaurants/{restaurant_id}/products", status_code=201, response_model=ProductRead)
async def create_product(
    restaurant_id: int, payload: ProductCreate, session: AsyncSession = Depends(get_session)
) -> Product:
    await get_restaurant_or_404(restaurant_id, session)
    await ensure_category_owned(payload.category_id, restaurant_id, session)
    product = Product(**payload.model_dump(), restaurant_id=restaurant_id)
    session.add(product)
    await session.commit()
    await session.refresh(product)
    return product


@router.get("/products/{product_id}", response_model=ProductDetailRead)
async def get_product(product_id: int, session: AsyncSession = Depends(get_session)) -> Product:
    return await get_product_or_404(product_id, session)


@router.put("/products/{product_id}", response_model=ProductRead)
async def update_product(
    product_id: int, payload: ProductUpdate, session: AsyncSession = Depends(get_session)
) -> Product:
    product = await get_product_or_404(product_id, session)
    if payload.category_id is not None:
        await ensure_category_owned(payload.category_id, product.restaurant_id, session)
    apply_product_data(product, payload.model_dump(exclude_unset=True))
    await session.commit()
    await session.refresh(product)
    return product


@router.delete("/products/{product_id}", status_code=204)
async def delete_product(product_id: int, session: AsyncSession = Depends(get_session)) -> None:
    product = await get_product_or_404(product_id, session)
    product.deleted_at = utcnow()
    await session.commit()


@router.post("/products/{product_id}/variants", status_code=201, response_model=VariantRead)
async def create_variant(
    product_id: int, payload: VariantCreate, session: AsyncSession = Depends(get_session)
) -> ProductVariant:
    product = await get_product_or_404(product_id, session)
    variant = ProductVariant(**payload.model_dump(), product_id=product.id)
    session.add(variant)
    await session.commit()
    await session.refresh(variant)
    return variant


@router.put("/variants/{variant_id}", response_model=VariantRead)
async def update_variant(
    variant_id: int, payload: VariantCreate, session: AsyncSession = Depends(get_session)
) -> ProductVariant:
    variant = await session.get(ProductVariant, variant_id)
    if variant is None:
        raise HTTPException(status_code=404, detail="Variação não encontrada")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(variant, field, value)
    await session.commit()
    await session.refresh(variant)
    return variant


@router.delete("/variants/{variant_id}", status_code=204)
async def delete_variant(variant_id: int, session: AsyncSession = Depends(get_session)) -> None:
    variant = await session.get(ProductVariant, variant_id)
    if variant is None:
        raise HTTPException(status_code=404, detail="Variação não encontrada")
    await session.delete(variant)
    await session.commit()


@router.get("/restaurants/{restaurant_id}/addons", response_model=list[AddonRead])
async def list_addons(restaurant_id: int, session: AsyncSession = Depends(get_session)) -> list[Addon]:
    await get_restaurant_or_404(restaurant_id, session)
    result = await session.scalars(
        select(Addon).where(Addon.restaurant_id == restaurant_id).order_by(Addon.name)
    )
    return list(result)


@router.post("/restaurants/{restaurant_id}/addons", status_code=201, response_model=AddonRead)
async def create_addon(
    restaurant_id: int, payload: AddonCreate, session: AsyncSession = Depends(get_session)
) -> Addon:
    await get_restaurant_or_404(restaurant_id, session)
    addon = Addon(**payload.model_dump(), restaurant_id=restaurant_id)
    session.add(addon)
    await session.commit()
    await session.refresh(addon)
    return addon


@router.put("/addons/{addon_id}", response_model=AddonRead)
async def update_addon(
    addon_id: int, payload: AddonCreate, session: AsyncSession = Depends(get_session)
) -> Addon:
    addon = await session.get(Addon, addon_id)
    if addon is None:
        raise HTTPException(status_code=404, detail="Adicional não encontrado")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(addon, field, value)
    await session.commit()
    await session.refresh(addon)
    return addon


@router.delete("/addons/{addon_id}", status_code=204)
async def delete_addon(addon_id: int, session: AsyncSession = Depends(get_session)) -> None:
    addon = await session.get(Addon, addon_id)
    if addon is None:
        raise HTTPException(status_code=404, detail="Adicional não encontrado")
    addon.status = "inactive"
    await session.commit()


@router.post("/products/{product_id}/addons", status_code=201, response_model=AddonRead)
async def attach_addon(
    product_id: int, payload: dict, session: AsyncSession = Depends(get_session)
) -> Addon:
    product = await get_product_or_404(product_id, session)
    addon_id = payload.get("addon_id")
    addon = await session.get(Addon, addon_id)
    if addon is None or addon.restaurant_id != product.restaurant_id:
        raise HTTPException(status_code=400, detail="Adicional inválido para este restaurante")
    if addon not in product.addons:
        product.addons.append(addon)
        await session.commit()
    return addon


@router.delete("/products/{product_id}/addons/{addon_id}", status_code=204)
async def detach_addon(product_id: int, addon_id: int, session: AsyncSession = Depends(get_session)) -> None:
    product = await get_product_or_404(product_id, session)
    addon = next((a for a in product.addons if a.id == addon_id), None)
    if addon is None:
        raise HTTPException(status_code=404, detail="Adicional não vinculado a este produto")
    product.addons.remove(addon)
    await session.commit()