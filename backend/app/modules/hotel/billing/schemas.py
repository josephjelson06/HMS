from datetime import datetime
from pydantic import BaseModel, ConfigDict
from uuid import UUID


class PlanOut(BaseModel):
    id: UUID
    name: str
    code: str
    description: str | None = None
    price_cents: int
    currency: str
    billing_interval: str
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class SubscriptionOut(BaseModel):
    id: UUID
    tenant_id: UUID
    plan_id: UUID
    status: str
    start_date: datetime | None = None
    current_period_start: datetime | None = None
    current_period_end: datetime | None = None
    cancel_at: datetime | None = None
    canceled_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class InvoiceOut(BaseModel):
    id: UUID
    tenant_id: UUID
    subscription_id: UUID
    invoice_number: str
    status: str
    amount_cents: int
    currency: str
    issued_at: datetime | None = None
    due_at: datetime | None = None
    paid_at: datetime | None = None
    notes: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class BillingSummary(BaseModel):
    subscription: SubscriptionOut | None = None
    plan: PlanOut | None = None
    invoices: list[InvoiceOut]
