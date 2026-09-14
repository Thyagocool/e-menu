from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.modules.order.models import Order, OrderItem

PENDING_STATUSES = ("RECEIVED", "CONFIRMED", "PREPARING", "READY", "DELIVERING")


class OrderRepository:
    async def create(self, session: AsyncSession, order: Order) -> Order:
        session.add(order)
        await session.flush()
        return order

    async def get(self, session: AsyncSession, order_id: int) -> Order | None:
        stmt = select(Order).where(Order.id == order_id).options(selectinload(Order.customer))
        return (await session.scalars(stmt)).first()

    async def list_by_restaurant(
        self, session: AsyncSession, restaurant_id: int, status: str | None = None
    ) -> list[Order]:
        stmt = (
            select(Order)
            .where(Order.restaurant_id == restaurant_id)
            .options(selectinload(Order.customer))
            .order_by(Order.id.desc())
        )
        if status:
            stmt = stmt.where(Order.status == status)
        return list((await session.scalars(stmt)).all())

    async def dashboard(self, session: AsyncSession, restaurant_id: int) -> dict:
        # "hoje" = início do dia em UTC; janela única para as métricas do painel
        day_start = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
        today = Order.created_at >= day_start

        orders_today = (
            await session.scalar(select(func.count()).select_from(Order).where(
                Order.restaurant_id == restaurant_id, today
            ))
        ) or 0
        revenue_raw = await session.scalar(
            select(func.coalesce(func.sum(Order.total), 0)).where(
                Order.restaurant_id == restaurant_id,
                today,
                Order.status == "COMPLETED",
            )
        )
        # sum de tabela vazia -> 0 (int); normalizar para "0.00"
        revenue_today = revenue_raw if revenue_raw else Decimal("0.00")
        pending = (
            await session.scalar(select(func.count()).select_from(Order).where(
                Order.restaurant_id == restaurant_id,
                Order.status.in_(PENDING_STATUSES),
            ))
        ) or 0

        ranking = (
            await session.execute(
                select(
                    OrderItem.product_name,
                    func.sum(OrderItem.quantity),
                    func.sum(OrderItem.line_total),
                )
                .join(Order, Order.id == OrderItem.order_id)
                .where(Order.restaurant_id == restaurant_id)
                .group_by(OrderItem.product_name)
                .order_by(func.sum(OrderItem.quantity).desc())
                .limit(5)
            )
        ).all()
        top_products = [
            {"name": name, "quantity": int(qty), "revenue": revenue}
            for name, qty, revenue in ranking
        ]
        return {
            "orders_today": orders_today,
            "revenue_today": revenue_today,
            "pending_orders": pending,
            "top_products": top_products,
        }