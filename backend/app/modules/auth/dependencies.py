from dataclasses import dataclass
from typing import Any
from uuid import UUID

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.permissions import has_permission
from app.core.database import get_session
from app.modules.auth.tokens import AccessTokenClaims, AccessTokenError, decode_access_token as decode_token_strict
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


async def require_access_token_claims(request: Request) -> AccessTokenClaims:
    """FastAPI dependency that extracts and validates typed JWT claims from the request.
    
    Use this for routes that only need auth identity (no DB lookup for user profile).
    For routes that need full user profile data, continue using get_current_user().
    """
    # First check if claims were already parsed by middleware
    claims = getattr(request.state, "token_claims", None)
    if isinstance(claims, AccessTokenClaims):
        return claims

    # Fall back to parsing from cookie
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Access token is required",
        )
    try:
        return decode_token_strict(token)
    except AccessTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token",
        )
