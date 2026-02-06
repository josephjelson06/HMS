from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from uuid import UUID


class ProfileOut(BaseModel):
    id: UUID
    email: str
    first_name: str | None = None
    last_name: str | None = None
    user_type: str
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class ProfileUpdate(BaseModel):
    first_name: str | None = Field(default=None, max_length=100)
    last_name: str | None = Field(default=None, max_length=100)
    current_password: str | None = Field(default=None, min_length=6)
    new_password: str | None = Field(default=None, min_length=6)
