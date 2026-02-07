"""Create refresh_token_families table

Revision ID: 0015_refresh_token_families
Revises: 0014_report_export_async_queue
Create Date: 2026-02-07 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0015_refresh_token_families"
down_revision = "0014_report_export_async_queue"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create refresh_token_families table
    op.create_table(
        "refresh_token_families",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("parent_family_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("refresh_token_families.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoke_reason", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    
    # Create indexes
    op.create_index("ix_refresh_token_families_tenant_id", "refresh_token_families", ["tenant_id"])
    op.create_index("ix_refresh_token_families_user_id", "refresh_token_families", ["user_id"])
    
    # Add family_id and rotated_at columns to refresh_tokens
    op.add_column(
        "refresh_tokens",
        sa.Column("family_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("refresh_token_families.id", ondelete="CASCADE"), nullable=True),
    )
    op.add_column(
        "refresh_tokens",
        sa.Column("rotated_at", sa.DateTime(timezone=True), nullable=True),
    )
    
    # Create index on family_id
    op.create_index("ix_refresh_tokens_family_id", "refresh_tokens", ["family_id"])


def downgrade() -> None:
    # Drop indexes and columns from refresh_tokens
    op.drop_index("ix_refresh_tokens_family_id", table_name="refresh_tokens")
    op.drop_column("refresh_tokens", "rotated_at")
    op.drop_column("refresh_tokens", "family_id")
    
    # Drop indexes and table
    op.drop_index("ix_refresh_token_families_user_id", table_name="refresh_token_families")
    op.drop_index("ix_refresh_token_families_tenant_id", table_name="refresh_token_families")
    op.drop_table("refresh_token_families")
