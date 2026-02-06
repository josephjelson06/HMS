from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class ImpersonationStartRequest(BaseModel):
    tenant_id: UUID | None = None
    target_user_id: UUID | None = None
    reason: str | None = Field(default=None, max_length=255)

    @model_validator(mode="after")
    def validate_target(self):
        if self.tenant_id is None and self.target_user_id is None:
            raise ValueError("Either tenant_id or target_user_id is required")
        return self


class UserOut(BaseModel):
    id: UUID
    email: EmailStr
    first_name: str | None = None
    last_name: str | None = None
    user_type: str
    tenant_id: UUID | None = None
    roles: list[str] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class TenantOut(BaseModel):
    id: UUID
    name: str
    slug: str

    model_config = ConfigDict(from_attributes=True)


class AuthResponse(BaseModel):
    user: UserOut
    permissions: list[str]
    tenant: TenantOut | None = None
    impersonation: dict[str, Any] | None = None


class LogoutResponse(BaseModel):
    success: bool = True
