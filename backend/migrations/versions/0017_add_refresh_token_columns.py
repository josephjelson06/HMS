"""Add family_id and rotated_at to refresh_tokens

Revision ID: 0017_add_refresh_token_columns
Revises: 0016_add_user_columns
Create Date: 2026-02-07 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = '0017_add_refresh_token_columns'
down_revision = '0016_add_user_columns'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add family_id — nullable first (will be backfilled in PR 6)
    op.add_column('refresh_tokens', sa.Column(
        'family_id', UUID(as_uuid=True), nullable=True
    ))
    op.create_foreign_key(
        'fk_refresh_tokens_family_id',
        'refresh_tokens', 'refresh_token_families',
        ['family_id'], ['id'],
        ondelete='CASCADE'
    )
    op.create_index('ix_refresh_tokens_family_id', 'refresh_tokens', ['family_id'])

    # Add rotated_at timestamp
    op.add_column('refresh_tokens', sa.Column(
        'rotated_at', sa.DateTime(timezone=True), nullable=True
    ))


def downgrade() -> None:
    op.drop_column('refresh_tokens', 'rotated_at')
    op.drop_index('ix_refresh_tokens_family_id', table_name='refresh_tokens')
    op.drop_constraint('fk_refresh_tokens_family_id', 'refresh_tokens', type_='foreignkey')
    op.drop_column('refresh_tokens', 'family_id')
