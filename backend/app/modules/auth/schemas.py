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
    must_reset_password: bool = False


class LogoutResponse(BaseModel):
    success: bool = True


# --- Password Management Schemas ---

class PasswordChangeRequest(BaseModel):
    """Request to change the current user's own password."""
    current_password: str
    new_password: str

class PasswordChangeResponse(BaseModel):
    """Response after successful password change."""
    message: str = "Password changed successfully. All sessions have been revoked."

class PasswordResetRequest(BaseModel):
    """Admin request to reset another user's password."""
    user_id: UUID
    
class PasswordResetResponse(BaseModel):
    """Response after admin password reset."""
    temporary_password: str
    message: str = "Password has been reset. User must change password on next login."

class InviteUserRequest(BaseModel):
    """Request to invite a new user."""
    email: str
    username: str
    user_type: str  # "platform" or "hotel"
    tenant_id: UUID
    role_names: list[str] = []

class InviteUserResponse(BaseModel):
    """Response after user invitation."""
    user_id: UUID
    email: str
    username: str
    temporary_password: str
    must_reset_password: bool = True
    message: str = "User invited successfully."

class IdentityCheckRequest(BaseModel):
    """Request to verify credentials without issuing tokens."""
    email: str
    password: str
    tenant_id: UUID | None = None

class IdentityCheckResponse(BaseModel):
    """Response for identity verification."""
    verified: bool
    user_id: UUID | None = None
    user_type: str | None = None

class AccessTokenVerifyResponse(BaseModel):
    """Response for access token introspection."""
    valid: bool
    user_id: UUID | None = None
    user_type: str | None = None
    tenant_id: UUID | None = None
    roles: list[str] = []
    expires_at: str | None = None
