"""Add report exports table

Revision ID: 0005_report_exports
Revises: 0004_invoices
Create Date: 2026-02-06 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0005_report_exports"
down_revision = "0004_invoices"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "report_exports",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("report_code", sa.String(length=80), nullable=False),
        sa.Column("export_format", sa.String(length=10), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False, server_default=sa.text("'completed'")),
        sa.Column(
            "requested_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
        ),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="SET NULL"),
        ),
        sa.Column("file_name", sa.String(length=255)),
        sa.Column("file_path", sa.String(length=500)),
        sa.Column("error_message", sa.Text()),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_report_exports_report_code", "report_exports", ["report_code"])


def downgrade() -> None:
    op.drop_index("ix_report_exports_report_code", table_name="report_exports")
    op.drop_table("report_exports")
