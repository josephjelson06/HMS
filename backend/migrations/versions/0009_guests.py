"""Add guests table

Revision ID: 0009_guests
Revises: 0008_platform_settings
Create Date: 2026-02-06 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0009_guests"
down_revision = "0008_platform_settings"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "guests",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("first_name", sa.String(length=100), nullable=False),
        sa.Column("last_name", sa.String(length=100), nullable=False),
        sa.Column("email", sa.String(length=255)),
        sa.Column("phone", sa.String(length=40)),
        sa.Column("status", sa.String(length=30), nullable=False, server_default=sa.text("'active'")),
        sa.Column("check_in_at", sa.DateTime(timezone=True)),
        sa.Column("check_out_at", sa.DateTime(timezone=True)),
        sa.Column("notes", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_guests_tenant_id", "guests", ["tenant_id"])
    op.create_index("ix_guests_email", "guests", ["email"])


def downgrade() -> None:
    op.drop_index("ix_guests_email", table_name="guests")
    op.drop_index("ix_guests_tenant_id", table_name="guests")
    op.drop_table("guests")
