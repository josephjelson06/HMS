from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from uuid import UUID


class HelpdeskCreate(BaseModel):
    tenant_id: UUID | None = None
    requester_name: str | None = Field(default=None, max_length=120)
    requester_email: str | None = Field(default=None, max_length=255)
    subject: str = Field(min_length=3, max_length=200)
    description: str | None = None
    status: str = Field(default="open", max_length=30)
    priority: str = Field(default="normal", max_length=30)
    assigned_to: UUID | None = None


class HelpdeskUpdate(BaseModel):
    tenant_id: UUID | None = None
    requester_name: str | None = Field(default=None, max_length=120)
    requester_email: str | None = Field(default=None, max_length=255)
    subject: str | None = Field(default=None, max_length=200)
    description: str | None = None
    status: str | None = Field(default=None, max_length=30)
    priority: str | None = Field(default=None, max_length=30)
    assigned_to: UUID | None = None
    closed_at: datetime | None = None


class HelpdeskOut(BaseModel):
    id: UUID
    tenant_id: UUID | None = None
    tenant_name: str | None = None
    requester_name: str | None = None
    requester_email: str | None = None
    subject: str
    description: str | None = None
    status: str
    priority: str
    assigned_to: UUID | None = None
    assignee_email: str | None = None
    closed_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class Pagination(BaseModel):
    page: int
    limit: int
    total: int


class HelpdeskListResponse(BaseModel):
    items: list[HelpdeskOut]
    pagination: Pagination
