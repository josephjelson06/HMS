from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from uuid import UUID


class TenantType(str, Enum):
    PLATFORM = "platform"
    HOTEL = "hotel"


@dataclass(frozen=True)
class AuthContext:
    """Immutable, auth-only identity object constructed from JWT claims.
    
    Use this for routes that only need authorization context (no user profile data).
    For routes that need email, first_name, last_name, use CurrentUser instead.
    
    This is constructed from the access token — NO database lookup required.
    """
    tenant_id: UUID | None
    tenant_type: TenantType
    user_id: UUID | None
    roles: tuple[str, ...]
    actor_user_id: UUID | None = None
    acting_as_user_id: UUID | None = None

    @property
    def is_impersonating(self) -> bool:
        """True if this context represents an impersonation session."""
        return self.actor_user_id is not None and self.acting_as_user_id is not None

    @property
    def effective_user_id(self) -> UUID | None:
        """The user ID to use for data operations — acting_as during impersonation, otherwise user_id."""
        return self.acting_as_user_id or self.user_id


def resolve_auth_context_from_claims(claims: dict | None) -> AuthContext | None:
    """Build an AuthContext from JWT claims (dict format).
    
    Returns None if claims are None (unauthenticated request).
    """
    if claims is None:
        return None

    # Extract user_type and convert to TenantType.
    # Transitional compatibility: legacy "admin" user_type should be treated as "platform".
    user_type_str = claims.get("user_type", "hotel") or "hotel"
    if user_type_str == "admin":
        user_type_str = "platform"
    try:
        tenant_type = TenantType(user_type_str)
    except ValueError:
        tenant_type = TenantType.HOTEL  # fallback

    # Extract tenant_id
    tenant_id_value = claims.get("tenant_id")
    tenant_id = UUID(tenant_id_value) if tenant_id_value else None

    # Extract user_id (from 'sub' claim)
    user_id_value = claims.get("sub")
    user_id = UUID(user_id_value) if user_id_value else None

    # Extract roles
    roles_value = claims.get("roles", [])
    roles = tuple(roles_value) if isinstance(roles_value, (list, tuple)) else ()

    # Extract impersonation fields
    impersonation = claims.get("impersonation")
    actor_user_id = None
    acting_as_user_id = None
    
    if impersonation and isinstance(impersonation, dict):
        actor_id = impersonation.get("actor_user_id")
        acting_id = impersonation.get("acting_as_user_id")
        actor_user_id = UUID(actor_id) if actor_id else None
        acting_as_user_id = UUID(acting_id) if acting_id else None

    return AuthContext(
        tenant_id=tenant_id,
        tenant_type=tenant_type,
        user_id=user_id,
        roles=roles,
        actor_user_id=actor_user_id,
        acting_as_user_id=acting_as_user_id,
    )
