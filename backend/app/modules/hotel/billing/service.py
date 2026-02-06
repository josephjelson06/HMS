from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.models.invoice import Invoice
from app.models.plan import Plan
from app.models.subscription import Subscription


class BillingService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_subscription(self, tenant_id: UUID) -> Subscription | None:
        stmt = (
            select(Subscription)
            .where(Subscription.tenant_id == tenant_id)
            .order_by(Subscription.created_at.desc())
            .limit(1)
        )
        return await self.session.scalar(stmt)

    async def get_plan(self, plan_id: UUID) -> Plan | None:
        return await self.session.get(Plan, plan_id)

    async def list_invoices(self, tenant_id: UUID, limit: int) -> list[Invoice]:
        limit = max(min(limit, 100), 1)
        stmt = (
            select(Invoice)
            .where(Invoice.tenant_id == tenant_id)
            .order_by(Invoice.issued_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_invoice(self, tenant_id: UUID, invoice_id: UUID) -> Invoice | None:
        stmt = select(Invoice).where(Invoice.id == invoice_id, Invoice.tenant_id == tenant_id)
        return await self.session.scalar(stmt)
