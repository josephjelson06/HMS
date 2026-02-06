"""Add rooms table

Revision ID: 0010_rooms
Revises: 0009_guests
Create Date: 2026-02-06 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0010_rooms"
down_revision = "0009_guests"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "rooms",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("number", sa.String(length=30), nullable=False),
        sa.Column("room_type", sa.String(length=80), nullable=False),
        sa.Column("floor", sa.String(length=20)),
        sa.Column("status", sa.String(length=30), nullable=False, server_default=sa.text("'available'")),
        sa.Column("capacity", sa.Integer()),
        sa.Column("rate_cents", sa.Integer()),
        sa.Column("currency", sa.String(length=3), nullable=False, server_default=sa.text("'USD'")),
        sa.Column("description", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_rooms_tenant_id", "rooms", ["tenant_id"])
    op.create_index("ix_rooms_tenant_number", "rooms", ["tenant_id", "number"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_rooms_tenant_number", table_name="rooms")
    op.drop_index("ix_rooms_tenant_id", table_name="rooms")
    op.drop_table("rooms")
