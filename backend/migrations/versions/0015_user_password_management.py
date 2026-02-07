"""Add username and must_reset_password to users

Revision ID: 0015_user_password_management
Revises: 0014_report_export_async_queue
Create Date: 2026-02-07 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "0015_user_password_management"
down_revision = "0014_report_export_async_queue"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add username column
    op.add_column(
        "users",
        sa.Column("username", sa.String(length=100), nullable=True),
    )
    
    # Add must_reset_password column with default False
    op.add_column(
        "users",
        sa.Column("must_reset_password", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )


def downgrade() -> None:
    op.drop_column("users", "must_reset_password")
    op.drop_column("users", "username")
