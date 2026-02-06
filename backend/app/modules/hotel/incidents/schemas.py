from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from uuid import UUID


class IncidentCreate(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    description: str | None = None
    status: str = Field(default="open", max_length=30)
    severity: str = Field(default="medium", max_length=30)
    category: str | None = Field(default=None, max_length=80)
    occurred_at: datetime | None = None
    resolved_at: datetime | None = None
    reported_by: UUID | None = None


class IncidentUpdate(BaseModel):
    title: str | None = Field(default=None, max_length=200)
    description: str | None = None
    status: str | None = Field(default=None, max_length=30)
    severity: str | None = Field(default=None, max_length=30)
    category: str | None = Field(default=None, max_length=80)
    occurred_at: datetime | None = None
    resolved_at: datetime | None = None
    reported_by: UUID | None = None


class IncidentOut(BaseModel):
    id: UUID
    tenant_id: UUID
    title: str
    description: str | None = None
    status: str
    severity: str
    category: str | None = None
    occurred_at: datetime | None = None
    resolved_at: datetime | None = None
    reported_by: UUID | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class Pagination(BaseModel):
    page: int
    limit: int
    total: int


class IncidentListResponse(BaseModel):
    items: list[IncidentOut]
    pagination: Pagination
