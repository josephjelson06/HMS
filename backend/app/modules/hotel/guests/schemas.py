from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from uuid import UUID


class GuestCreate(BaseModel):
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    email: str | None = Field(default=None, max_length=255)
    phone: str | None = Field(default=None, max_length=40)
    status: str = Field(default="active", max_length=30)
    check_in_at: datetime | None = None
    check_out_at: datetime | None = None
    notes: str | None = None


class GuestUpdate(BaseModel):
    first_name: str | None = Field(default=None, max_length=100)
    last_name: str | None = Field(default=None, max_length=100)
    email: str | None = Field(default=None, max_length=255)
    phone: str | None = Field(default=None, max_length=40)
    status: str | None = Field(default=None, max_length=30)
    check_in_at: datetime | None = None
    check_out_at: datetime | None = None
    notes: str | None = None


class GuestOut(BaseModel):
    id: UUID
    tenant_id: UUID
    first_name: str
    last_name: str
    email: str | None = None
    phone: str | None = None
    status: str
    check_in_at: datetime | None = None
    check_out_at: datetime | None = None
    notes: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class Pagination(BaseModel):
    page: int
    limit: int
    total: int


class GuestListResponse(BaseModel):
    items: list[GuestOut]
    pagination: Pagination
