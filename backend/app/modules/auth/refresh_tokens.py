"""Refresh token family management utilities.

This module provides utilities for managing refresh token families,
including revocation of all tokens for a user.
"""
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.token import RefreshToken


async def revoke_all_refresh_token_families(
    session: AsyncSession,
    *,
    user_id: UUID,
    reason: str | None = None,
) -> int:
    """Revoke all refresh token families for a user.
    
    This is used when:
    - User changes their password
    - Admin resets a user's password
    - Account security is compromised
    
    Args:
        session: Database session
        user_id: The user whose tokens should be revoked
        reason: Optional reason for revocation (e.g., "password_changed", "password_reset_by_admin")
    
    Returns:
        Number of tokens revoked
    """
    # Get all non-revoked tokens for this user
    stmt = select(RefreshToken).where(
        RefreshToken.user_id == user_id,
        RefreshToken.revoked_at.is_(None),
    )
    result = await session.execute(stmt)
    tokens = result.scalars().all()
    
    # Revoke each token
    now = datetime.now(timezone.utc)
    count = 0
    for token in tokens:
        token.revoked_at = now
        session.add(token)
        count += 1
    
    return count
