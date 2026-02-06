from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from uuid import UUID


class RoomCreate(BaseModel):
    number: str = Field(min_length=1, max_length=30)
    room_type: str = Field(min_length=1, max_length=80)
    floor: str | None = Field(default=None, max_length=20)
    status: str = Field(default="available", max_length=30)
    capacity: int | None = Field(default=None, ge=1)
    rate_cents: int | None = Field(default=None, ge=0)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    description: str | None = None


class RoomUpdate(BaseModel):
    number: str | None = Field(default=None, max_length=30)
    room_type: str | None = Field(default=None, max_length=80)
    floor: str | None = Field(default=None, max_length=20)
    status: str | None = Field(default=None, max_length=30)
    capacity: int | None = Field(default=None, ge=1)
    rate_cents: int | None = Field(default=None, ge=0)
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    description: str | None = None


class RoomOut(BaseModel):
    id: UUID
    tenant_id: UUID
    number: str
    room_type: str
    floor: str | None = None
    status: str
    capacity: int | None = None
    rate_cents: int | None = None
    currency: str
    description: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class Pagination(BaseModel):
    page: int
    limit: int
    total: int


class RoomListResponse(BaseModel):
    items: list[RoomOut]
    pagination: Pagination
