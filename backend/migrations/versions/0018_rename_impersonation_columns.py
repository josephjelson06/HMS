"""Rename impersonation_sessions columns and add refresh_token_family_id

Revision ID: 0018_rename_impersonation_columns
Revises: 0017_add_refresh_token_columns
Create Date: 2026-02-07 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = '0018_rename_impersonation_columns'
down_revision = '0017_add_refresh_token_columns'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Rename columns for consistency with AuthModule naming
    op.alter_column('impersonation_sessions', 'admin_user_id', new_column_name='actor_user_id')
    op.alter_column('impersonation_sessions', 'target_user_id', new_column_name='acting_as_user_id')

    # Rename target_tenant_id to tenant_id if it exists
    # (HMS uses 'target_tenant_id' — check and rename)
    try:
        op.alter_column('impersonation_sessions', 'target_tenant_id', new_column_name='tenant_id')
    except Exception:
        pass  # Column might already be named 'tenant_id'

    # Add refresh_token_family_id FK
    op.add_column('impersonation_sessions', sa.Column(
        'refresh_token_family_id', UUID(as_uuid=True), nullable=True
    ))
    op.create_foreign_key(
        'fk_impersonation_sessions_family_id',
        'impersonation_sessions', 'refresh_token_families',
        ['refresh_token_family_id'], ['id'],
        ondelete='SET NULL'
    )


def downgrade() -> None:
    op.drop_constraint('fk_impersonation_sessions_family_id', 'impersonation_sessions', type_='foreignkey')
    op.drop_column('impersonation_sessions', 'refresh_token_family_id')
    try:
        op.alter_column('impersonation_sessions', 'tenant_id', new_column_name='target_tenant_id')
    except Exception:
        pass
    op.alter_column('impersonation_sessions', 'acting_as_user_id', new_column_name='target_user_id')
    op.alter_column('impersonation_sessions', 'actor_user_id', new_column_name='admin_user_id')
