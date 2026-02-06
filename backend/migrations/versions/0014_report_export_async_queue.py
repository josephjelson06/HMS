"""Add report export async queue fields

Revision ID: 0014_report_export_async_queue
Revises: 0013_refresh_token_impersonation
Create Date: 2026-02-06 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0014_report_export_async_queue"
down_revision = "0013_refresh_token_impersonation"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "report_exports",
        sa.Column("scope", sa.String(length=20), nullable=True),
    )
    op.add_column(
        "report_exports",
        sa.Column("filters", postgresql.JSONB(), nullable=True),
    )

    op.execute(
        """
        UPDATE report_exports
        SET scope = CASE WHEN tenant_id IS NULL THEN 'admin' ELSE 'hotel' END
        WHERE scope IS NULL
        """
    )

    op.alter_column(
        "report_exports",
        "scope",
        existing_type=sa.String(length=20),
        nullable=False,
        server_default=sa.text("'admin'"),
    )
    op.alter_column(
        "report_exports",
        "status",
        existing_type=sa.String(length=30),
        nullable=False,
        server_default=sa.text("'pending'"),
    )

    op.create_index("ix_report_exports_status", "report_exports", ["status"])


def downgrade() -> None:
    op.drop_index("ix_report_exports_status", table_name="report_exports")
    op.alter_column(
        "report_exports",
        "status",
        existing_type=sa.String(length=30),
        nullable=False,
        server_default=sa.text("'completed'"),
    )
    op.drop_column("report_exports", "filters")
    op.drop_column("report_exports", "scope")
