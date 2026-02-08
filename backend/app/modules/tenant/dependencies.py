from __future__ import annotations

from uuid import UUID

from fastapi import Depends, HTTPException, Request, status

from app.modules.tenant.context import AuthContext


async def require_auth_context(request: Request) -> AuthContext:
    """FastAPI dependency that returns the AuthContext for the current request.
    
    The AuthContext is set by the TenantContextMiddleware (or by the JWT middleware).
    This dependency does NOT hit the database — it reads from request.state.
    
    Raises 401 if no auth context is available (unauthenticated request).
    """
    auth_context = getattr(request.state, "auth_context", None)
    if auth_context is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required.",
        )
    return auth_context


async def require_authenticated_user_id(
    auth_context: AuthContext = Depends(require_auth_context),
) -> UUID:
    """FastAPI dependency that returns the effective user ID.
    
    During impersonation, returns acting_as_user_id.
    Otherwise, returns user_id.
    
    Raises 401 if user_id is not available.
    """
    effective_id = auth_context.effective_user_id
    if effective_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authenticated user ID is required.",
        )
    return effective_id
