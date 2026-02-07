"""Refresh token family system with rotation and reuse detection.

This module implements OAuth 2.0 refresh token rotation with family-based
lifecycle management. Key features:

- Each login creates a RefreshTokenFamily (container for a session lineage)
- On refresh, old token is marked rotated_at, new token issued in SAME family
- If a rotated token is reused (replay attack), ENTIRE family is revoked
- Structured token format: rt1.{tenant_id}.{random} allows pre-DB tenant extraction
- On logout, the family is revoked (not just the single token)

Reference: https://github.com/josephjelson06/AuthModule
"""
from __future__ import annotations

import hashlib
import secrets
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import select, update, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.token import RefreshToken, RefreshTokenFamily


REFRESH_TOKEN_BYTES = 32
REFRESH_TOKEN_VERSION = "rt1"


class RefreshTokenError(Exception):
    """Base error for refresh token operations."""
    def __init__(self, detail: str, status_code: int = 401):
        super().__init__(detail)
        self.detail = detail
        self.status_code = status_code


class RefreshTokenReuseDetectedError(RefreshTokenError):
    """Raised when a previously-rotated refresh token is presented again (replay attack)."""
    def __init__(self):
        super().__init__(
            detail="Refresh token reuse detected. All sessions in this family have been revoked.",
            status_code=401,
        )


@dataclass(frozen=True)
class RefreshTokenIssueResult:
    """Result of issuing a new refresh token."""
    raw_token: str
    family_id: UUID
    token_id: UUID


@dataclass(frozen=True)
class RefreshTokenRotateResult:
    """Result of rotating a refresh token."""
    raw_token: str
    family_id: UUID
    token_id: UUID
    user_id: UUID
    tenant_id: UUID


def build_refresh_token(tenant_id: UUID) -> str:
    """Build a structured refresh token: rt1.{tenant_uuid}.{random_bytes}
    
    The tenant_id prefix allows extracting tenant context BEFORE hitting the DB,
    enabling tenant-scoped queries on the refresh_tokens table.
    """
    random_part = secrets.token_urlsafe(REFRESH_TOKEN_BYTES)
    return f"{REFRESH_TOKEN_VERSION}.{tenant_id}.{random_part}"


def hash_refresh_token(raw_token: str) -> str:
    """SHA-256 hash of the raw refresh token for storage."""
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


def parse_tenant_id_from_refresh_token(raw_token: str) -> UUID:
    """Extract tenant_id from the structured token without DB lookup.
    
    Token format: rt1.{tenant_uuid}.{random}
    """
    parts = raw_token.split(".", 2)
    if len(parts) != 3 or parts[0] != REFRESH_TOKEN_VERSION:
        raise RefreshTokenError("Refresh token format is invalid.", status_code=401)
    try:
        return UUID(parts[1])
    except (ValueError, TypeError) as exc:
        raise RefreshTokenError("Refresh token tenant_id is malformed.", status_code=401) from exc


async def issue_new_refresh_token_family(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    user_id: UUID,
    refresh_token_days: int,
    created_by_user_id: UUID | None = None,
    parent_family_id: UUID | None = None,
) -> RefreshTokenIssueResult:
    """Create a new refresh token family and issue the first token in it.
    
    Called on: login, impersonation start, impersonation stop.
    """
    # Create the family
    family = RefreshTokenFamily(
        tenant_id=tenant_id,
        user_id=user_id,
        parent_family_id=parent_family_id,
        created_by_user_id=created_by_user_id,
    )
    session.add(family)
    await session.flush()  # Get family.id

    # Issue first token in the family
    raw_token = build_refresh_token(tenant_id)
    token_hash = hash_refresh_token(raw_token)
    now = datetime.now(UTC)
    expires_at = now + timedelta(days=refresh_token_days)

    token = RefreshToken(
        tenant_id=tenant_id,
        user_id=user_id,
        family_id=family.id,
        jti=str(uuid.uuid4()),  # Generate JTI for backward compatibility
        token_hash=token_hash,
        expires_at=expires_at,
    )
    session.add(token)
    await session.flush()

    return RefreshTokenIssueResult(
        raw_token=raw_token,
        family_id=family.id,
        token_id=token.id,
    )


async def rotate_refresh_token(
    session: AsyncSession,
    *,
    raw_token: str,
    refresh_token_days: int,
) -> RefreshTokenRotateResult:
    """Rotate a refresh token: mark the old one as rotated, issue a new one in the same family.
    
    If the presented token was already rotated (reuse), revoke the entire family.
    """
    token_hash = hash_refresh_token(raw_token)
    now = datetime.now(UTC)

    # Look up the token by hash
    result = await session.execute(
        select(RefreshToken).where(RefreshToken.token_hash == token_hash)
    )
    db_token = result.scalar_one_or_none()

    if db_token is None:
        raise RefreshTokenError("Refresh token not found.")

    # Check if the family is revoked
    family_result = await session.execute(
        select(RefreshTokenFamily).where(RefreshTokenFamily.id == db_token.family_id)
    )
    family = family_result.scalar_one_or_none()
    if family is None or family.revoked_at is not None:
        raise RefreshTokenError("Refresh token family has been revoked.")

    # Check if token is expired
    if db_token.expires_at < now:
        raise RefreshTokenError("Refresh token has expired.")

    # Check if token was already revoked individually
    if db_token.revoked_at is not None:
        raise RefreshTokenError("Refresh token has been revoked.")

    # REUSE DETECTION: if this token was already rotated, it's a replay attack
    if db_token.rotated_at is not None:
        # Revoke the entire family
        await _revoke_family(session, family_id=db_token.family_id, reason="reuse_detected")
        raise RefreshTokenReuseDetectedError()

    # Mark the old token as rotated
    db_token.rotated_at = now

    # Issue a new token in the same family
    tenant_id = db_token.tenant_id
    new_raw_token = build_refresh_token(tenant_id)
    new_token_hash = hash_refresh_token(new_raw_token)
    new_expires_at = now + timedelta(days=refresh_token_days)

    new_token = RefreshToken(
        tenant_id=tenant_id,
        user_id=db_token.user_id,
        family_id=db_token.family_id,
        jti=str(uuid.uuid4()),  # Generate JTI for backward compatibility
        token_hash=new_token_hash,
        expires_at=new_expires_at,
    )
    session.add(new_token)
    await session.flush()

    return RefreshTokenRotateResult(
        raw_token=new_raw_token,
        family_id=db_token.family_id,
        token_id=new_token.id,
        user_id=db_token.user_id,
        tenant_id=tenant_id,
    )


async def revoke_family_by_refresh_token(
    session: AsyncSession,
    *,
    raw_token: str,
    reason: str = "logout",
) -> tuple[UUID | None, int]:
    """Revoke the entire family that a refresh token belongs to.
    
    Returns (family_id, count_of_revoked_tokens).
    Called on: logout.
    """
    token_hash = hash_refresh_token(raw_token)

    result = await session.execute(
        select(RefreshToken).where(RefreshToken.token_hash == token_hash)
    )
    db_token = result.scalar_one_or_none()

    if db_token is None:
        raise RefreshTokenError("Refresh token not found.")

    family_id = db_token.family_id
    count = await _revoke_family(session, family_id=family_id, reason=reason)
    return family_id, count


async def revoke_all_refresh_token_families(
    session: AsyncSession,
    *,
    user_id: UUID,
    reason: str,
) -> int:
    """Revoke ALL refresh token families for a user.
    
    Called on: password change, password reset.
    Returns the count of families revoked.
    """
    now = datetime.now(UTC)

    # Find all active families for this user
    result = await session.execute(
        select(RefreshTokenFamily).where(
            and_(
                RefreshTokenFamily.user_id == user_id,
                RefreshTokenFamily.revoked_at.is_(None),
            )
        )
    )
    families = result.scalars().all()

    count = 0
    for family in families:
        family.revoked_at = now
        family.revoke_reason = reason
        count += 1

    # Also revoke all individual tokens for this user that aren't already revoked
    await session.execute(
        update(RefreshToken)
        .where(
            and_(
                RefreshToken.user_id == user_id,
                RefreshToken.revoked_at.is_(None),
            )
        )
        .values(revoked_at=now)
    )

    return count


async def _revoke_family(
    session: AsyncSession,
    *,
    family_id: UUID,
    reason: str,
) -> int:
    """Internal: revoke a single family and all its tokens."""
    now = datetime.now(UTC)

    # Revoke the family
    result = await session.execute(
        select(RefreshTokenFamily).where(RefreshTokenFamily.id == family_id)
    )
    family = result.scalar_one_or_none()
    if family is not None and family.revoked_at is None:
        family.revoked_at = now
        family.revoke_reason = reason

    # Revoke all tokens in the family
    token_result = await session.execute(
        update(RefreshToken)
        .where(
            and_(
                RefreshToken.family_id == family_id,
                RefreshToken.revoked_at.is_(None),
            )
        )
        .values(revoked_at=now)
        .returning(RefreshToken.id)
    )
    # Count revoked tokens
    revoked_ids = token_result.all()
    return len(revoked_ids)
