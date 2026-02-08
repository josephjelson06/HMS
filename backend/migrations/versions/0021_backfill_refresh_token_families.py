"""Backfill existing refresh tokens into families

Revision ID: 0021_backfill_refresh_token_families
Revises: 0020_migrate_user_type
Create Date: 2026-02-07 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


revision = "0021_backfill_refresh_token_families"
down_revision = "0020_migrate_user_type"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # For each existing refresh token without a family_id,
    # create a separate family (one family per token)
    # We can't reconstruct the original rotation chains, so each token gets its own family
    op.execute("""
        -- Create one family for each orphaned token
        INSERT INTO refresh_token_families (tenant_id, user_id, created_by_user_id, created_at, updated_at)
        SELECT rt.tenant_id, rt.user_id, rt.user_id, rt.issued_at, rt.issued_at
        FROM refresh_tokens rt
        WHERE rt.family_id IS NULL;
        
        -- Update each token to point to a newly created family
        -- We use ROW_NUMBER to assign families in the order they were created
        WITH numbered_tokens AS (
            SELECT 
                rt.id as token_id,
                ROW_NUMBER() OVER (ORDER BY rt.issued_at) as token_num
            FROM refresh_tokens rt
            WHERE rt.family_id IS NULL
        ),
        numbered_families AS (
            SELECT 
                rtf.id as family_id,
                ROW_NUMBER() OVER (ORDER BY rtf.created_at) as family_num
            FROM refresh_token_families rtf
            WHERE NOT EXISTS (
                SELECT 1 FROM refresh_tokens rt2 
                WHERE rt2.family_id = rtf.id
            )
        )
        UPDATE refresh_tokens rt
        SET family_id = nf.family_id
        FROM numbered_tokens nt
        JOIN numbered_families nf ON nt.token_num = nf.family_num
        WHERE rt.id = nt.token_id;
    """)


def downgrade() -> None:
    # Set family_id back to NULL
    op.execute("UPDATE refresh_tokens SET family_id = NULL")
    # Delete all families
    op.execute("DELETE FROM refresh_token_families")
