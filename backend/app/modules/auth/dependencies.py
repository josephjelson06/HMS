from dataclasses import dataclass
from typing import Any
from uuid import UUID

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.permissions import build_scoped_permission, has_permission
from app.core.database import get_session
from app.repositories.permission import PermissionRepository
from app.repositories.user import UserRepository


@dataclass
class CurrentUser:
    id: UUID
    email: str
    first_name: str | None
    last_name: str | None
    user_type: str
    tenant_id: UUID | None
    roles: list[str]
    permissions: list[str]
    impersonation: dict[str, Any] | None


async def get_current_user(
    request: Request,
    session: AsyncSession = Depends(get_session),
) -> CurrentUser:
    payload = request.state.token_payload
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    user_repo = UserRepository(session)
    perm_repo = PermissionRepository(session)

    user = await user_repo.get_by_id(UUID(user_id))
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    permissions = await perm_repo.get_permissions_for_user(user.id)
    roles = await perm_repo.get_role_names_for_user(user.id)
    tenant_id = payload.get("tenant_id")
    impersonation = payload.get("impersonation")

    if user.user_type == "hotel":
        if not tenant_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Tenant context missing")
        if user.tenant_id and str(user.tenant_id) != str(tenant_id):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Tenant context mismatch")

    return CurrentUser(
        id=user.id,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        user_type=user.user_type,
        tenant_id=user.tenant_id,
        roles=roles,
        permissions=permissions,
        impersonation=impersonation,
    )


def require_permission(permission_code: str):
    async def checker(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if not has_permission(current_user.permissions, permission_code):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
        return current_user

    return checker


def require_tenant_permission(resource: str, action: str):
    """FastAPI dependency factory that checks permissions auto-scoped to the caller's tenant type.
    
    Usage:
        @router.post("/rooms")
        async def create_room(
            _: str = Depends(require_tenant_permission("rooms", "create")),
            current_user: CurrentUser = Depends(get_current_user),
        ):
            ...
    
    This automatically resolves to "hotel:rooms:create" or "platform:rooms:create"
    based on the current user's user_type/tenant_type.
    
    Existing routes using Depends(require_permission("admin:hotels:read")) continue to work.
    New routes should prefer this auto-scoping version.
    """
    async def _check_permission(
        current_user = Depends(get_current_user),
    ) -> str:
        # Determine the tenant type from the user's user_type
        # After PR 5, user_type is "platform" or "hotel"
        tenant_type = current_user.user_type
        required = build_scoped_permission(tenant_type, resource, action)
        
        if not has_permission(current_user.permissions, required):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: {required}",
            )
        return required
    
    return _check_permission


async def get_effective_permissions(request: Request, current_user = Depends(get_current_user)) -> frozenset[str]:
    """Get the effective permissions for the current user, cached per-request.
    
    Returns a frozenset of permission strings resolved from the user's roles.
    """
    cached = getattr(request.state, "_effective_permissions", None)
    if cached is not None:
        return cached
    
    permissions = frozenset(current_user.permissions)
    request.state._effective_permissions = permissions
    return permissions
