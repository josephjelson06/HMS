from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from uuid import UUID


class KioskCreate(BaseModel):
    tenant_id: UUID
    name: str = Field(min_length=2, max_length=120)
    location: str | None = Field(default=None, max_length=255)
    status: str = Field(default="active", max_length=30)
    device_id: str | None = Field(default=None, max_length=80)


class KioskUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=120)
    location: str | None = Field(default=None, max_length=255)
    status: str | None = Field(default=None, max_length=30)
    device_id: str | None = Field(default=None, max_length=80)
    rotate_token: bool | None = None


class KioskOut(BaseModel):
    id: UUID
    tenant_id: UUID
    tenant_name: str | None = None
    name: str
    location: str | None = None
    status: str
    device_id: str | None = None
    token_last4: str | None = None
    last_seen_at: datetime | None = None
    issued_token: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class Pagination(BaseModel):
    page: int
    limit: int
    total: int


class KioskListResponse(BaseModel):
    items: list[KioskOut]
    pagination: Pagination
