from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from uuid import UUID


class SubscriptionCreate(BaseModel):
    tenant_id: UUID
    plan_id: UUID
    status: str = Field(default="active", max_length=30)
    start_date: datetime | None = None
    current_period_end: datetime | None = None
    cancel_at: datetime | None = None


class SubscriptionUpdate(BaseModel):
    tenant_id: UUID | None = None
    plan_id: UUID | None = None
    status: str | None = Field(default=None, max_length=30)
    current_period_end: datetime | None = None
    cancel_at: datetime | None = None
    canceled_at: datetime | None = None


class SubscriptionOut(BaseModel):
    id: UUID
    tenant_id: UUID
    tenant_name: str | None = None
    plan_id: UUID
    plan_name: str | None = None
    plan_code: str | None = None
    status: str
    start_date: datetime | None = None
    current_period_start: datetime | None = None
    current_period_end: datetime | None = None
    cancel_at: datetime | None = None
    canceled_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class Pagination(BaseModel):
    page: int
    limit: int
    total: int


class SubscriptionListResponse(BaseModel):
    items: list[SubscriptionOut]
    pagination: Pagination
