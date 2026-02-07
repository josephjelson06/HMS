import re
from typing import Iterable


def has_permission(user_permissions: Iterable[str], required: str) -> bool:
    if required in user_permissions:
        return True

    req_parts = required.split(":")

    for perm in user_permissions:
        if perm == "*":
            return True

        perm_parts = perm.split(":")

        # Case 1: Prefix wildcard e.g. "hotel:*" matches "hotel:rooms:create"
        if perm_parts[-1] == "*" and len(perm_parts) < len(req_parts):
            if perm_parts[:-1] == req_parts[: len(perm_parts) - 1]:
                return True

        # Case 2: Component wildcard e.g. "hotel:*:create" matches "hotel:rooms:create"
        if len(perm_parts) == len(req_parts):
            match = True
            for p, r in zip(perm_parts, req_parts):
                if p != "*" and p != r:
                    match = False
                    break
            if match:
                return True

    return False


# --- New additions from AuthModule ---

PERMISSION_PATTERN = re.compile(r"^[a-z][a-z0-9_]*(?::[a-z][a-z0-9_]*)*(?::\*)?$")

FIXED_ROLES = (
    "platform_super_admin",
    "platform_admin",
    "hotel_admin",
    "hotel_manager",
    "hotel_front_desk",
    "hotel_housekeeping",
    "hotel_maintenance",
    "hotel_auditor",
)

PLATFORM_ROLES = {"platform_super_admin", "platform_admin"}
HOTEL_ROLES = {"hotel_admin", "hotel_manager", "hotel_front_desk", "hotel_housekeeping", "hotel_maintenance", "hotel_auditor"}


def validate_permission_key(key: str) -> str:
    """Validate that a permission key matches the expected format.
    
    Valid examples: 'hotel:rooms:create', 'platform:users:read', 'hotel:*'
    Invalid examples: 'Hotel:Rooms', '123:abc', '', 'hotel rooms create'
    
    Returns the key if valid, raises ValueError if not.
    """
    if not PERMISSION_PATTERN.match(key):
        raise ValueError(
            f"Permission key '{key}' does not match the required pattern. "
            f"Expected format: 'scope:resource:action' using lowercase alphanumeric and underscores."
        )
    return key


def permission_implies(held: str, required: str) -> bool:
    """Check if a held permission implies a required permission.
    
    This wraps has_permission() for single-permission checks.
    """
    return has_permission([held], required)


def ensure_role_scope_match(role_name: str, tenant_type: str) -> None:
    """Ensure a role is valid for the given tenant type.
    
    Prevents cross-scope role assignment (e.g., hotel role on platform tenant).
    Raises ValueError if there's a mismatch.
    """
    if role_name in PLATFORM_ROLES and tenant_type != "platform":
        raise ValueError(
            f"Role '{role_name}' is a platform role and cannot be assigned in a '{tenant_type}' tenant."
        )
    if role_name in HOTEL_ROLES and tenant_type != "hotel":
        raise ValueError(
            f"Role '{role_name}' is a hotel role and cannot be assigned in a '{tenant_type}' tenant."
        )


def build_scoped_permission(tenant_type: str, resource: str, action: str) -> str:
    """Build a fully-scoped permission string from tenant type, resource, and action.
    
    Example: build_scoped_permission("platform", "hotels", "read") -> "platform:hotels:read"
    Example: build_scoped_permission("hotel", "rooms", "create") -> "hotel:rooms:create"
    """
    return f"{tenant_type}:{resource}:{action}"
