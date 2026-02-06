from pydantic import BaseModel, ConfigDict, Field
from uuid import UUID


class PermissionOut(BaseModel):
    id: UUID
    code: str
    name: str
    description: str | None = None
    resource: str
    action: str

    model_config = ConfigDict(from_attributes=True)


class RoleCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    display_name: str = Field(min_length=2, max_length=100)
    description: str | None = None
    permissions: list[str] = Field(default_factory=list)


class RoleUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=100)
    display_name: str | None = Field(default=None, max_length=100)
    description: str | None = None
    permissions: list[str] | None = None


class RoleOut(BaseModel):
    id: UUID
    name: str
    display_name: str
    description: str | None = None
    is_system: bool
    tenant_id: UUID | None = None
    permissions: list[str] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)
