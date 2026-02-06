from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from uuid import UUID


class HotelRoleOut(BaseModel):
    id: UUID
    name: str
    display_name: str
    description: str | None = None

    model_config = ConfigDict(from_attributes=True)


class HotelUserCreate(BaseModel):
    email: str = Field(min_length=5, max_length=255)
    password: str = Field(min_length=6, max_length=128)
    first_name: str | None = Field(default=None, max_length=100)
    last_name: str | None = Field(default=None, max_length=100)
    role_id: UUID
    is_active: bool = True


class HotelUserUpdate(BaseModel):
    email: str | None = Field(default=None, max_length=255)
    password: str | None = Field(default=None, min_length=6, max_length=128)
    first_name: str | None = Field(default=None, max_length=100)
    last_name: str | None = Field(default=None, max_length=100)
    role_id: UUID | None = None
    is_active: bool | None = None


class HotelUserOut(BaseModel):
    id: UUID
    email: str
    first_name: str | None = None
    last_name: str | None = None
    is_active: bool
    roles: list[str]
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class Pagination(BaseModel):
    page: int
    limit: int
    total: int


class HotelUserListResponse(BaseModel):
    items: list[HotelUserOut]
    pagination: Pagination
