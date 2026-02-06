import uuid
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.models.invoice import Invoice
from app.models.plan import Plan
from app.models.subscription import Subscription
from app.models.tenant import Tenant


def generate_invoice_number() -> str:
    return f"INV-{uuid.uuid4().hex[:8].upper()}"


class InvoiceService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_invoices(
        self, page: int, limit: int
    ) -> tuple[list[tuple[Invoice, str | None, str | None, str | None]], int]:
        page = max(page, 1)
        limit = max(min(limit, 100), 1)

        total = await self.session.scalar(select(func.count()).select_from(Invoice))
        stmt = (
            select(Invoice, Tenant.name, Plan.name, Plan.code)
            .join(Tenant, Tenant.id == Invoice.tenant_id)
            .join(Subscription, Subscription.id == Invoice.subscription_id)
            .join(Plan, Plan.id == Subscription.plan_id)
            .order_by(Invoice.created_at.desc())
            .offset((page - 1) * limit)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        items = result.all()
        return items, int(total or 0)

    async def get(self, invoice_id: UUID) -> Invoice | None:
        return await self.session.get(Invoice, invoice_id)

    async def get_names(
        self, invoice: Invoice
    ) -> tuple[str | None, str | None, str | None]:
        tenant = await self.session.get(Tenant, invoice.tenant_id)
        subscription = await self.session.get(Subscription, invoice.subscription_id)
        plan = (
            await self.session.get(Plan, subscription.plan_id) if subscription else None
        )
        return (
            tenant.name if tenant else None,
            plan.name if plan else None,
            plan.code if plan else None,
        )

    async def create(self, payload) -> Invoice:
        tenant = await self.session.get(Tenant, payload.tenant_id)
        if not tenant:
            raise ValueError("Tenant not found")

        subscription = await self.session.get(Subscription, payload.subscription_id)
        if not subscription:
            raise ValueError("Subscription not found")
        if subscription.tenant_id != tenant.id:
            raise ValueError("Subscription does not belong to tenant")

        invoice_number = payload.invoice_number or generate_invoice_number()
        existing = await self.session.scalar(
            select(Invoice).where(Invoice.invoice_number == invoice_number)
        )
        if existing:
            raise ValueError("Invoice number already exists")

        issued_at = payload.issued_at or datetime.now(timezone.utc)

        invoice = Invoice(
            tenant_id=tenant.id,
            subscription_id=subscription.id,
            invoice_number=invoice_number,
            status=payload.status,
            amount_cents=payload.amount_cents,
            currency=payload.currency.upper(),
            issued_at=issued_at,
            due_at=payload.due_at,
            paid_at=payload.paid_at,
            notes=payload.notes,
        )
        self.session.add(invoice)
        await self.session.commit()
        await self.session.refresh(invoice)
        return invoice

    async def update(self, invoice: Invoice, payload) -> Invoice:
        next_tenant_id = payload.tenant_id or invoice.tenant_id

        if payload.tenant_id is not None:
            tenant = await self.session.get(Tenant, payload.tenant_id)
            if not tenant:
                raise ValueError("Tenant not found")

        if payload.subscription_id is not None:
            subscription = await self.session.get(Subscription, payload.subscription_id)
            if not subscription:
                raise ValueError("Subscription not found")
        else:
            subscription = await self.session.get(Subscription, invoice.subscription_id)

        if subscription and subscription.tenant_id != next_tenant_id:
            raise ValueError("Subscription does not belong to tenant")

        if payload.tenant_id is not None:
            invoice.tenant_id = payload.tenant_id
        if payload.subscription_id is not None:
            invoice.subscription_id = payload.subscription_id

        if payload.invoice_number is not None:
            invoice_number = payload.invoice_number.strip()
            if not invoice_number:
                raise ValueError("Invalid invoice number")
            existing = await self.session.scalar(
                select(Invoice).where(
                    Invoice.invoice_number == invoice_number, Invoice.id != invoice.id
                )
            )
            if existing:
                raise ValueError("Invoice number already exists")
            invoice.invoice_number = invoice_number

        if payload.status is not None:
            invoice.status = payload.status
        if payload.amount_cents is not None:
            invoice.amount_cents = payload.amount_cents
        if payload.currency is not None:
            invoice.currency = payload.currency.upper()
        if payload.issued_at is not None:
            invoice.issued_at = payload.issued_at
        if payload.due_at is not None:
            invoice.due_at = payload.due_at
        if payload.paid_at is not None:
            invoice.paid_at = payload.paid_at
        if payload.notes is not None:
            invoice.notes = payload.notes

        self.session.add(invoice)
        await self.session.commit()
        await self.session.refresh(invoice)
        return invoice

    async def delete(self, invoice: Invoice) -> None:
        await self.session.delete(invoice)
        await self.session.commit()
