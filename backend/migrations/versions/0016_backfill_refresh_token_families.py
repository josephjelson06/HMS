"""Backfill existing refresh tokens into families

Revision ID: 0016_backfill_refresh_token_families
Revises: 0015_refresh_token_families
Create Date: 2026-02-07 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


revision = "0016_backfill_refresh_token_families"
down_revision = "0015_refresh_token_families"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # For each existing refresh token without a family_id,
    # create a family and assign it
    # We'll create one family per token for simplicity since we can't reconstruct the rotation chain
    op.execute("""
        -- Insert a new family for each orphaned token
        INSERT INTO refresh_token_families (tenant_id, user_id, created_by_user_id, created_at, updated_at)
        SELECT DISTINCT rt.tenant_id, rt.user_id, rt.user_id, rt.issued_at, rt.issued_at
        FROM refresh_tokens rt
        WHERE rt.family_id IS NULL;
        
        -- Update refresh_tokens to link to the newly created families
        -- This is a simplified approach: each existing token gets its own family
        WITH token_family_mapping AS (
            SELECT 
                rt.id as token_id,
                (
                    SELECT rtf.id
                    FROM refresh_token_families rtf
                    WHERE rtf.user_id = rt.user_id 
                      AND rtf.tenant_id = rt.tenant_id
                      AND NOT EXISTS (
                          SELECT 1 FROM refresh_tokens rt2 
                          WHERE rt2.family_id = rtf.id
                      )
                    LIMIT 1
                ) as family_id
            FROM refresh_tokens rt
            WHERE rt.family_id IS NULL
        )
        UPDATE refresh_tokens rt
        SET family_id = tfm.family_id
        FROM token_family_mapping tfm
        WHERE rt.id = tfm.token_id AND tfm.family_id IS NOT NULL;
        
        -- For any remaining tokens still without a family (edge case), create individual families
        INSERT INTO refresh_token_families (tenant_id, user_id, created_by_user_id, created_at, updated_at)
        SELECT rt.tenant_id, rt.user_id, rt.user_id, rt.issued_at, rt.issued_at
        FROM refresh_tokens rt
        WHERE rt.family_id IS NULL;
        
        -- Final assignment pass for any stragglers
        UPDATE refresh_tokens rt
        SET family_id = (
            SELECT rtf.id
            FROM refresh_token_families rtf
            WHERE rtf.user_id = rt.user_id 
              AND rtf.tenant_id = rt.tenant_id
              AND NOT EXISTS (
                  SELECT 1 FROM refresh_tokens rt2 
                  WHERE rt2.family_id = rtf.id
              )
            LIMIT 1
        )
        WHERE rt.family_id IS NULL;
    """)


def downgrade() -> None:
    # Set family_id back to NULL
    op.execute("UPDATE refresh_tokens SET family_id = NULL")
    # Delete all families
    op.execute("DELETE FROM refresh_token_families")
