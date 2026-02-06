from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from uuid import UUID


class PlanCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    code: str | None = Field(default=None, max_length=80)
    description: str | None = None
    price_cents: int = Field(ge=0)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    billing_interval: str = Field(default="monthly", max_length=20)
    is_active: bool = True


class PlanUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=120)
    code: str | None = Field(default=None, max_length=80)
    description: str | None = None
    price_cents: int | None = Field(default=None, ge=0)
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    billing_interval: str | None = Field(default=None, max_length=20)
    is_active: bool | None = None


class PlanOut(BaseModel):
    id: UUID
    name: str
    code: str
    description: str | None = None
    price_cents: int
    currency: str
    billing_interval: str
    is_active: bool
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class Pagination(BaseModel):
    page: int
    limit: int
    total: int


class PlanListResponse(BaseModel):
    items: list[PlanOut]
    pagination: Pagination
