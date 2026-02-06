"""Add kiosks table

Revision ID: 0006_kiosks
Revises: 0005_report_exports
Create Date: 2026-02-06 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0006_kiosks"
down_revision = "0005_report_exports"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "kiosks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("location", sa.String(length=255)),
        sa.Column("status", sa.String(length=30), nullable=False, server_default=sa.text("'active'")),
        sa.Column("device_id", sa.String(length=80)),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("token_last4", sa.String(length=4)),
        sa.Column("last_seen_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_kiosks_tenant_id", "kiosks", ["tenant_id"])
    op.create_index("ix_kiosks_device_id", "kiosks", ["device_id"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_kiosks_device_id", table_name="kiosks")
    op.drop_index("ix_kiosks_tenant_id", table_name="kiosks")
    op.drop_table("kiosks")
