"""Add username, domain, must_reset_password, invited_at to users

Revision ID: 0016_add_user_columns
Revises: 0015_create_refresh_token_families
Create Date: 2026-02-07 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = '0016_add_user_columns'
down_revision = '0015_create_refresh_token_families'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add username — nullable first, will backfill
    op.add_column('users', sa.Column('username', sa.String(120), nullable=True))
    # Backfill username from email (take part before @)
    op.execute("UPDATE users SET username = split_part(email, '@', 1) WHERE username IS NULL")
    # Now set NOT NULL
    op.alter_column('users', 'username', nullable=False)

    op.add_column('users', sa.Column('domain', sa.String(120), nullable=True))
    op.add_column('users', sa.Column('must_reset_password', sa.Boolean(), nullable=False, server_default=sa.text('false')))
    op.add_column('users', sa.Column('invited_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()))

    # Widen email from 255 to 320 (RFC 5321 max)
    op.alter_column('users', 'email', type_=sa.String(320))

    # Add unique constraint on (tenant_id, username)
    op.create_unique_constraint('uq_users_tenant_username', 'users', ['tenant_id', 'username'])


def downgrade() -> None:
    op.drop_constraint('uq_users_tenant_username', 'users', type_='unique')
    op.alter_column('users', 'email', type_=sa.String(255))
    op.drop_column('users', 'invited_at')
    op.drop_column('users', 'must_reset_password')
    op.drop_column('users', 'domain')
    op.drop_column('users', 'username')
