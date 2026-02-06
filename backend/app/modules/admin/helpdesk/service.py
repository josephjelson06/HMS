from datetime import datetime, timezone
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.models.helpdesk_ticket import HelpdeskTicket
from app.models.tenant import Tenant
from app.models.user import User


class HelpdeskService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list(
        self,
        page: int,
        limit: int,
        status: str | None = None,
        priority: str | None = None,
        tenant_id: UUID | None = None,
    ) -> tuple[list[tuple[HelpdeskTicket, str | None, str | None]], int]:
        page = max(page, 1)
        limit = max(min(limit, 100), 1)

        total_stmt = select(func.count()).select_from(HelpdeskTicket)
        stmt = (
            select(HelpdeskTicket, Tenant.name, User.email)
            .join(Tenant, Tenant.id == HelpdeskTicket.tenant_id, isouter=True)
            .join(User, User.id == HelpdeskTicket.assigned_to, isouter=True)
            .order_by(HelpdeskTicket.created_at.desc())
        )
        if status:
            total_stmt = total_stmt.where(HelpdeskTicket.status == status)
            stmt = stmt.where(HelpdeskTicket.status == status)
        if priority:
            total_stmt = total_stmt.where(HelpdeskTicket.priority == priority)
            stmt = stmt.where(HelpdeskTicket.priority == priority)
        if tenant_id:
            total_stmt = total_stmt.where(HelpdeskTicket.tenant_id == tenant_id)
            stmt = stmt.where(HelpdeskTicket.tenant_id == tenant_id)

        total = await self.session.scalar(total_stmt)
        stmt = stmt.offset((page - 1) * limit).limit(limit)
        result = await self.session.execute(stmt)
        return result.all(), int(total or 0)

    async def get(self, ticket_id: UUID) -> HelpdeskTicket | None:
        return await self.session.get(HelpdeskTicket, ticket_id)

    async def create(self, payload) -> HelpdeskTicket:
        tenant_id = payload.tenant_id
        if tenant_id:
            tenant = await self.session.get(Tenant, tenant_id)
            if not tenant:
                raise ValueError("Tenant not found")

        if payload.assigned_to:
            user = await self.session.get(User, payload.assigned_to)
            if not user:
                raise ValueError("Assigned user not found")

        ticket = HelpdeskTicket(
            tenant_id=tenant_id,
            requester_name=payload.requester_name,
            requester_email=payload.requester_email,
            subject=payload.subject,
            description=payload.description,
            status=payload.status,
            priority=payload.priority,
            assigned_to=payload.assigned_to,
        )
        self.session.add(ticket)
        await self.session.commit()
        await self.session.refresh(ticket)
        return ticket

    async def update(self, ticket: HelpdeskTicket, payload) -> HelpdeskTicket:
        if payload.tenant_id is not None:
            if payload.tenant_id:
                tenant = await self.session.get(Tenant, payload.tenant_id)
                if not tenant:
                    raise ValueError("Tenant not found")
            ticket.tenant_id = payload.tenant_id

        if payload.assigned_to is not None:
            if payload.assigned_to:
                user = await self.session.get(User, payload.assigned_to)
                if not user:
                    raise ValueError("Assigned user not found")
            ticket.assigned_to = payload.assigned_to

        if payload.requester_name is not None:
            ticket.requester_name = payload.requester_name
        if payload.requester_email is not None:
            ticket.requester_email = payload.requester_email
        if payload.subject is not None:
            ticket.subject = payload.subject
        if payload.description is not None:
            ticket.description = payload.description
        if payload.status is not None:
            ticket.status = payload.status
            if payload.status.lower() in {"closed", "resolved"} and ticket.closed_at is None:
                ticket.closed_at = datetime.now(timezone.utc)
        if payload.priority is not None:
            ticket.priority = payload.priority
        if payload.closed_at is not None:
            ticket.closed_at = payload.closed_at

        self.session.add(ticket)
        await self.session.commit()
        await self.session.refresh(ticket)
        return ticket

    async def delete(self, ticket: HelpdeskTicket) -> None:
        await self.session.delete(ticket)
        await self.session.commit()
