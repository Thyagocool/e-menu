"""Sprint 6: pedido com snapshot comercial dos itens.

Revision ID: 0006
Revises: 0005
Create Date: 2026-09-14
"""
from datetime import datetime, timezone

import sqlalchemy as sa
from alembic import op

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def upgrade() -> None:
    op.create_table(
        "orders",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("restaurant_id", sa.Integer(), sa.ForeignKey("restaurants.id"), nullable=False, index=True),
        sa.Column("customer_id", sa.Integer(), sa.ForeignKey("customers.id"), nullable=False, index=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="RECEIVED"),
        sa.Column("delivery_type", sa.String(length=20), nullable=False, server_default="retirada"),
        sa.Column("address", sa.String(length=300), nullable=True),
        sa.Column("payment_method", sa.String(length=20), nullable=False, server_default="pix"),
        sa.Column("delivery_fee", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("subtotal", sa.Numeric(10, 2), nullable=False),
        sa.Column("total", sa.Numeric(10, 2), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_table(
        "order_items",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("order_id", sa.Integer(), sa.ForeignKey("orders.id"), nullable=False, index=True),
        sa.Column("product_id", sa.Integer(), sa.ForeignKey("products.id"), nullable=True),
        sa.Column("product_name", sa.String(length=150), nullable=False),
        sa.Column("variant_name", sa.String(length=100), nullable=True),
        sa.Column("unit_price", sa.Numeric(10, 2), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("line_total", sa.Numeric(10, 2), nullable=False),
        sa.Column("addons", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("order_items")
    op.drop_table("orders")