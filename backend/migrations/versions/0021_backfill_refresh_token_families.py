"""Backfill existing refresh tokens into families

Revision ID: 0021_backfill_refresh_token_families
Revises: 0020_migrate_user_type
Create Date: 2026-02-07 00:00:00.000000

"""
from alembic import op

revision = "0021_backfill_refresh_token_families"
down_revision = "0020_migrate_user_type"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Backfill ONLY tenant-scoped refresh tokens (hotel users).
    # Platform tokens have tenant_id NULL and remain on the legacy non-family path.
    #
    # Deterministic + idempotent mapping: use refresh_tokens.id as refresh_token_families.id.
    # This avoids asyncpg multi-statement issues and avoids fragile row_number matching.

    op.execute(
        """
        INSERT INTO refresh_token_families (id, tenant_id, user_id, created_by_user_id, created_at, updated_at)
        SELECT rt.id, rt.tenant_id, rt.user_id, rt.user_id, rt.issued_at, rt.issued_at
        FROM refresh_tokens rt
        WHERE rt.family_id IS NULL
          AND rt.tenant_id IS NOT NULL
        ON CONFLICT (id) DO NOTHING
        """
    )

    op.execute(
        """
        UPDATE refresh_tokens
        SET family_id = id
        WHERE family_id IS NULL
          AND tenant_id IS NOT NULL
        """
    )


def downgrade() -> None:
    # Set family_id back to NULL
    op.execute("UPDATE refresh_tokens SET family_id = NULL")
    # Delete all families
    op.execute("DELETE FROM refresh_token_families")
