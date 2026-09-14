from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.infra.database import get_session
from src.modules.cart.schemas import CartItemCreate, CartItemUpdate, CartRead
from src.modules.cart.usecases import CartService

router = APIRouter(tags=["cart"])
service = CartService()


@router.get("/customers/{customer_id}/cart", response_model=CartRead)
async def get_cart(customer_id: int, session: AsyncSession = Depends(get_session)) -> CartRead:
    return await service.get_cart(session, customer_id)


@router.post("/cart/items", response_model=CartRead, status_code=201)
async def add_item(payload: CartItemCreate, session: AsyncSession = Depends(get_session)) -> CartRead:
    return await service.add_item(
        session,
        payload.customer_id,
        payload.product_id,
        payload.variant_id,
        payload.quantity,
        payload.addon_ids,
    )


@router.put("/cart/items/{item_id}", response_model=CartRead)
async def update_quantity(
    item_id: int, payload: CartItemUpdate, session: AsyncSession = Depends(get_session)
) -> CartRead:
    return await service.update_quantity(session, item_id, payload.quantity)


@router.delete("/cart/items/{item_id}", response_model=CartRead)
async def remove_item(item_id: int, session: AsyncSession = Depends(get_session)) -> CartRead:
    return await service.remove_item(session, item_id)


@router.delete("/customers/{customer_id}/cart", response_model=CartRead)
async def clear_cart(customer_id: int, session: AsyncSession = Depends(get_session)) -> CartRead:
    return await service.clear(session, customer_id)