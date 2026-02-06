from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.token import RefreshToken


class RefreshTokenRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        *,
        user_id,
        tenant_id,
        jti: str,
        token_hash: str,
        expires_in_days: int,
        ip_address: str | None,
        user_agent: str | None,
        impersonation_session_id: UUID | None = None,
        impersonated_by_user_id: UUID | None = None,
    ) -> RefreshToken:
        expires_at = datetime.now(timezone.utc) + timedelta(days=expires_in_days)
        token = RefreshToken(
            user_id=user_id,
            tenant_id=tenant_id,
            jti=jti,
            token_hash=token_hash,
            expires_at=expires_at,
            ip_address=ip_address,
            user_agent=user_agent,
            impersonation_session_id=impersonation_session_id,
            impersonated_by_user_id=impersonated_by_user_id,
        )
        self.session.add(token)
        return token

    async def get_by_hash(self, token_hash: str) -> RefreshToken | None:
        return await self.session.scalar(select(RefreshToken).where(RefreshToken.token_hash == token_hash))

    async def revoke(self, token: RefreshToken, replaced_by_jti: str | None = None) -> None:
        token.revoked_at = datetime.now(timezone.utc)
        token.replaced_by_jti = replaced_by_jti
        self.session.add(token)
