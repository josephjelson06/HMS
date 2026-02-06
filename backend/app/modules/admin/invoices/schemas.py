from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from uuid import UUID


class InvoiceCreate(BaseModel):
    tenant_id: UUID
    subscription_id: UUID
    invoice_number: str | None = Field(default=None, max_length=50)
    status: str = Field(default="issued", max_length=30)
    amount_cents: int = Field(ge=0)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    issued_at: datetime | None = None
    due_at: datetime | None = None
    paid_at: datetime | None = None
    notes: str | None = None


class InvoiceUpdate(BaseModel):
    tenant_id: UUID | None = None
    subscription_id: UUID | None = None
    invoice_number: str | None = Field(default=None, max_length=50)
    status: str | None = Field(default=None, max_length=30)
    amount_cents: int | None = Field(default=None, ge=0)
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    issued_at: datetime | None = None
    due_at: datetime | None = None
    paid_at: datetime | None = None
    notes: str | None = None


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
    tenant_name: str | None = None
    plan_name: str | None = None
    plan_code: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class Pagination(BaseModel):
    page: int
    limit: int
    total: int


class InvoiceListResponse(BaseModel):
    items: list[InvoiceOut]
    pagination: Pagination
