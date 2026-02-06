"""Add refresh token impersonation metadata

Revision ID: 0013_refresh_token_impersonation
Revises: 0012_hotel_settings
Create Date: 2026-02-06 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0013_refresh_token_impersonation"
down_revision = "0012_hotel_settings"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "refresh_tokens",
        sa.Column(
            "impersonation_session_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("impersonation_sessions.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.add_column(
        "refresh_tokens",
        sa.Column(
            "impersonated_by_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.create_index(
        "ix_refresh_tokens_impersonation_session_id",
        "refresh_tokens",
        ["impersonation_session_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_refresh_tokens_impersonation_session_id", table_name="refresh_tokens")
    op.drop_column("refresh_tokens", "impersonated_by_user_id")
    op.drop_column("refresh_tokens", "impersonation_session_id")
