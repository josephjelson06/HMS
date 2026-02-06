from pydantic import BaseModel, ConfigDict, Field
from uuid import UUID
from datetime import datetime


class HotelCreate(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    slug: str | None = Field(default=None, max_length=100)
    status: str = Field(default="active", max_length=50)
    subscription_tier: str | None = Field(default=None, max_length=50)


class HotelUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=255)
    slug: str | None = Field(default=None, max_length=100)
    status: str | None = Field(default=None, max_length=50)
    subscription_tier: str | None = Field(default=None, max_length=50)


class HotelOut(BaseModel):
    id: UUID
    name: str
    slug: str
    status: str
    subscription_tier: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class Pagination(BaseModel):
    page: int
    limit: int
    total: int


class HotelListResponse(BaseModel):
    items: list[HotelOut]
    pagination: Pagination
