"""Migrate user_type 'admin' to 'platform'

Revision ID: 0020_migrate_user_type
Revises: 0019_rename_audit_columns
Create Date: 2026-02-07 00:00:00.000000

"""
from alembic import op

revision = '0020_migrate_user_type'
down_revision = '0019_rename_audit_columns'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Data migration: rename user_type value
    op.execute("UPDATE users SET user_type = 'platform' WHERE user_type = 'admin'")

    # Drop old CHECK constraint if it exists and create new one
    # The constraint name may vary — use try/except
    try:
        op.drop_constraint('ck_users_user_type', 'users', type_='check')
    except Exception:
        pass
    op.create_check_constraint(
        'ck_users_user_type',
        'users',
        "user_type IN ('platform', 'hotel')"
    )


def downgrade() -> None:
    op.execute("UPDATE users SET user_type = 'admin' WHERE user_type = 'platform'")
    try:
        op.drop_constraint('ck_users_user_type', 'users', type_='check')
    except Exception:
        pass
    op.create_check_constraint(
        'ck_users_user_type',
        'users',
        "user_type IN ('admin', 'hotel')"
    )
