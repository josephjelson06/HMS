"""Add hotel settings table

Revision ID: 0012_hotel_settings
Revises: 0011_incidents
Create Date: 2026-02-06 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0012_hotel_settings"
down_revision = "0011_incidents"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "hotel_settings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("key", sa.String(length=100), nullable=False),
        sa.Column("value", postgresql.JSONB(), nullable=True),
        sa.Column("description", sa.String(length=255)),
        sa.Column(
            "updated_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.UniqueConstraint("tenant_id", "key", name="uq_hotel_settings_tenant_key"),
    )
    op.create_index("ix_hotel_settings_tenant_id", "hotel_settings", ["tenant_id"])
    op.create_index("ix_hotel_settings_key", "hotel_settings", ["key"])


def downgrade() -> None:
    op.drop_index("ix_hotel_settings_key", table_name="hotel_settings")
    op.drop_index("ix_hotel_settings_tenant_id", table_name="hotel_settings")
    op.drop_table("hotel_settings")
