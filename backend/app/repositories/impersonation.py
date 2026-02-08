from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import ImpersonationSession


class ImpersonationSessionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        *,
        actor_user_id: UUID,
        acting_as_user_id: UUID,
        tenant_id: UUID,
        reason: str | None,
        ip_address: str | None,
    ) -> ImpersonationSession:
        session = ImpersonationSession(
            actor_user_id=actor_user_id,
            acting_as_user_id=acting_as_user_id,
            tenant_id=tenant_id,
            reason=reason,
            ip_address=ip_address,
        )
        self.session.add(session)
        await self.session.flush()
        await self.session.refresh(session)
        return session

    async def get_active_by_id(self, session_id: UUID) -> ImpersonationSession | None:
        stmt = select(ImpersonationSession).where(
            ImpersonationSession.id == session_id,
            ImpersonationSession.ended_at.is_(None),
        )
        return await self.session.scalar(stmt)

    async def get_active_for_actor(self, actor_user_id: UUID) -> ImpersonationSession | None:
        stmt = (
            select(ImpersonationSession)
            .where(
                ImpersonationSession.actor_user_id == actor_user_id,
                ImpersonationSession.ended_at.is_(None),
            )
            .order_by(ImpersonationSession.started_at.desc())
            .limit(1)
        )
        return await self.session.scalar(stmt)

    async def end(self, session: ImpersonationSession) -> None:
        session.ended_at = datetime.now(timezone.utc)
        self.session.add(session)
