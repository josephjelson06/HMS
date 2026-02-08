"""Rename audit_logs columns for AuthModule consistency

Revision ID: 0019_rename_audit_columns
Revises: 0018_rename_impersonation_columns
Create Date: 2026-02-07 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = '0019_rename_audit_columns'
down_revision = '0018_rename_impersonation_columns'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Rename user_id → actor_user_id
    op.alter_column('audit_logs', 'user_id', new_column_name='actor_user_id')

    # Add acting_as_user_id for impersonation context tracking
    op.add_column('audit_logs', sa.Column(
        'acting_as_user_id', UUID(as_uuid=True), nullable=True
    ))
    op.create_foreign_key(
        'fk_audit_logs_acting_as_user_id',
        'audit_logs', 'users',
        ['acting_as_user_id'], ['id'],
        ondelete='SET NULL'
    )
    op.create_index('ix_audit_logs_acting_as_user_id', 'audit_logs', ['acting_as_user_id'])

    # Rename changes → metadata (JSONB column)
    op.alter_column('audit_logs', 'changes', new_column_name='metadata')


def downgrade() -> None:
    op.alter_column('audit_logs', 'metadata', new_column_name='changes')
    op.drop_index('ix_audit_logs_acting_as_user_id', table_name='audit_logs')
    op.drop_constraint('fk_audit_logs_acting_as_user_id', 'audit_logs', type_='foreignkey')
    op.drop_column('audit_logs', 'acting_as_user_id')
    op.alter_column('audit_logs', 'actor_user_id', new_column_name='user_id')
