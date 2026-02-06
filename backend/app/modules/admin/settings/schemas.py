from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from uuid import UUID


JsonValue = dict | list | str | int | float | bool | None


class SettingCreate(BaseModel):
    key: str = Field(min_length=2, max_length=100)
    value: JsonValue = None
    description: str | None = Field(default=None, max_length=255)


class SettingUpdate(BaseModel):
    value: JsonValue = None
    description: str | None = Field(default=None, max_length=255)


class SettingOut(BaseModel):
    id: UUID
    key: str
    value: JsonValue = None
    description: str | None = None
    updated_by: UUID | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class Pagination(BaseModel):
    page: int
    limit: int
    total: int


class SettingListResponse(BaseModel):
    items: list[SettingOut]
    pagination: Pagination
