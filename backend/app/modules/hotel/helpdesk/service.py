from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.models.helpdesk_ticket import HelpdeskTicket


class HotelHelpdeskService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list(self, tenant_id: UUID, limit: int) -> list[HelpdeskTicket]:
        limit = max(min(limit, 100), 1)
        stmt = (
            select(HelpdeskTicket)
            .where(HelpdeskTicket.tenant_id == tenant_id)
            .order_by(HelpdeskTicket.created_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def create(self, tenant_id: UUID, payload) -> HelpdeskTicket:
        ticket = HelpdeskTicket(
            tenant_id=tenant_id,
            requester_name=payload.requester_name,
            requester_email=payload.requester_email,
            subject=payload.subject,
            description=payload.description,
            status="open",
            priority=payload.priority,
        )
        self.session.add(ticket)
        await self.session.commit()
        await self.session.refresh(ticket)
        return ticket
