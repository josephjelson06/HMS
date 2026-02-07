from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_session
from app.models.tenant import Tenant
from app.modules.auth.dependencies import CurrentUser, get_current_user, require_permission
from app.modules.auth.schemas import (
    AccessTokenVerifyResponse,
    AuthResponse,
    IdentityCheckRequest,
    IdentityCheckResponse,
    ImpersonationStartRequest,
    InviteUserRequest,
    InviteUserResponse,
    LoginRequest,
    LogoutResponse,
    PasswordChangeRequest,
    PasswordChangeResponse,
    PasswordResetRequest,
    PasswordResetResponse,
    TenantOut,
    UserOut,
)
from app.modules.auth.service import AuthService
from app.modules.audit.hooks import audit_event_stub
from app.repositories.user import UserRepository


router = APIRouter()


def set_auth_cookies(response: Response, access_token: str, refresh_token: str, csrf_token: str) -> None:
    response.set_cookie(
        "access_token",
        access_token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
        max_age=settings.jwt_access_ttl_minutes * 60,
        path="/",
        domain=settings.cookie_domain,
    )
    response.set_cookie(
        "refresh_token",
        refresh_token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
        max_age=settings.jwt_refresh_ttl_days * 24 * 60 * 60,
        path="/",
        domain=settings.cookie_domain,
    )
    response.set_cookie(
        "csrf_token",
        csrf_token,
        httponly=False,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
        max_age=settings.jwt_refresh_ttl_days * 24 * 60 * 60,
        path="/",
        domain=settings.cookie_domain,
    )


def clear_auth_cookies(response: Response) -> None:
    response.delete_cookie("access_token", path="/", domain=settings.cookie_domain)
    response.delete_cookie("refresh_token", path="/", domain=settings.cookie_domain)
    response.delete_cookie("csrf_token", path="/", domain=settings.cookie_domain)


@router.post("/login", response_model=AuthResponse)
async def login(
    payload: LoginRequest,
    response: Response,
    request: Request,
    session: AsyncSession = Depends(get_session),
) -> AuthResponse:
    service = AuthService(session, request)
    result = await service.login(payload.email, payload.password)
    set_auth_cookies(response, result.access_token, result.refresh_token, result.csrf_token)
    return result.response


@router.post("/refresh", response_model=AuthResponse)
async def refresh(
    response: Response,
    request: Request,
    session: AsyncSession = Depends(get_session),
) -> AuthResponse:
    refresh_token = request.cookies.get("refresh_token")
    service = AuthService(session, request)
    result = await service.refresh(refresh_token)
    set_auth_cookies(response, result.access_token, result.refresh_token, result.csrf_token)
    return result.response


@router.post("/logout", response_model=LogoutResponse)
async def logout(
    response: Response,
    request: Request,
    session: AsyncSession = Depends(get_session),
) -> LogoutResponse:
    refresh_token = request.cookies.get("refresh_token")
    service = AuthService(session, request)
    await service.logout(refresh_token)
    clear_auth_cookies(response)
    return LogoutResponse()


@router.post(
    "/impersonation/start",
    response_model=AuthResponse,
    dependencies=[Depends(require_permission("admin:impersonation:start"))],
)
async def start_impersonation(
    payload: ImpersonationStartRequest,
    response: Response,
    request: Request,
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> AuthResponse:
    if current_user.user_type != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admins can impersonate")
    if current_user.impersonation and current_user.impersonation.get("active"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Impersonation already active")

    service = AuthService(session, request)
    result = await service.start_impersonation(
        admin_user_id=current_user.id,
        tenant_id=payload.tenant_id,
        target_user_id=payload.target_user_id,
        reason=payload.reason,
    )
    set_auth_cookies(response, result.access_token, result.refresh_token, result.csrf_token)
    return result.response


@router.post("/impersonation/stop", response_model=AuthResponse)
async def stop_impersonation(
    response: Response,
    request: Request,
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> AuthResponse:
    service = AuthService(session, request)
    result = await service.stop_impersonation(
        acting_user_id=current_user.id,
        impersonation=current_user.impersonation,
        current_refresh_token=request.cookies.get("refresh_token"),
    )
    set_auth_cookies(response, result.access_token, result.refresh_token, result.csrf_token)
    return result.response


@router.get("/me", response_model=AuthResponse)
async def me(
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> AuthResponse:
    tenant = None
    if current_user.tenant_id:
        tenant_obj = await session.get(Tenant, current_user.tenant_id)
        if tenant_obj:
            tenant = TenantOut.model_validate(tenant_obj)

    return AuthResponse(
        user=UserOut(
            id=current_user.id,
            email=current_user.email,
            first_name=current_user.first_name,
            last_name=current_user.last_name,
            user_type=current_user.user_type,
            tenant_id=current_user.tenant_id,
            roles=current_user.roles,
        ),
        permissions=current_user.permissions,
        tenant=tenant,
        impersonation=current_user.impersonation,
    )


@router.post("/password/change", response_model=PasswordChangeResponse)
async def change_password(
    payload: PasswordChangeRequest,
    request: Request,
    current_user = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Change the current user's password. Revokes all active sessions."""
    service = AuthService(session, request)
    await service.change_password(
        user_id=current_user.id,
        current_password=payload.current_password,
        new_password=payload.new_password,
    )
    
    await audit_event_stub(
        action="password.changed",
        session=session,
        metadata={"user_id": str(current_user.id)},
    )
    
    return PasswordChangeResponse()


@router.post("/password/reset", response_model=PasswordResetResponse)
async def reset_password(
    payload: PasswordResetRequest,
    request: Request,
    current_user = Depends(get_current_user),
    _: str = Depends(require_permission("admin:users:manage")),
    session: AsyncSession = Depends(get_session),
):
    """Admin resets another user's password. Returns a temporary password."""
    service = AuthService(session, request)
    temp_password = await service.reset_password(
        target_user_id=payload.user_id,
        admin_user_id=current_user.id,
    )
    
    await audit_event_stub(
        action="password.reset",
        session=session,
        metadata={
            "target_user_id": str(payload.user_id),
            "reset_by": str(current_user.id),
        },
    )
    
    return PasswordResetResponse(temporary_password=temp_password)


@router.post("/users/invite", response_model=InviteUserResponse)
async def invite_user(
    payload: InviteUserRequest,
    request: Request,
    current_user = Depends(get_current_user),
    _: str = Depends(require_permission("admin:users:create")),
    session: AsyncSession = Depends(get_session),
):
    """Invite a new user with a temporary password."""
    service = AuthService(session, request)
    user, temp_password = await service.invite_user(
        email=payload.email,
        username=payload.username,
        user_type=payload.user_type,
        tenant_id=payload.tenant_id,
    )
    
    await audit_event_stub(
        action="user.invited",
        session=session,
        metadata={
            "invited_user_id": str(user.id),
            "email": payload.email,
            "user_type": payload.user_type,
            "invited_by": str(current_user.id),
        },
    )
    
    return InviteUserResponse(
        user_id=user.id,
        email=user.email,
        username=user.username,
        temporary_password=temp_password,
    )


@router.post("/identity/check", response_model=IdentityCheckResponse)
async def identity_check(
    payload: IdentityCheckRequest,
    session: AsyncSession = Depends(get_session),
):
    """Verify credentials without issuing tokens.
    
    Useful for confirming identity before sensitive operations.
    """
    from app.core.security import verify_password_constant_time
    
    # Look up user
    user_repo = UserRepository(session)
    user = await user_repo.get_by_email(payload.email)
    
    password_hash = user.password_hash if user else None
    verified = verify_password_constant_time(payload.password, password_hash)
    
    if verified and user and user.is_active:
        return IdentityCheckResponse(
            verified=True,
            user_id=user.id,
            user_type=user.user_type,
        )
    
    return IdentityCheckResponse(verified=False)


@router.get("/access-token/verify", response_model=AccessTokenVerifyResponse)
async def verify_access_token(
    request: Request,
):
    """Introspect the current access token and return its claims.
    
    Returns valid=false if no token or token is invalid/expired.
    """
    from app.core.security import decode_access_token
    
    token = request.cookies.get("access_token")
    if not token:
        return AccessTokenVerifyResponse(valid=False)
    
    try:
        claims = decode_access_token(token)
        if not claims:
            return AccessTokenVerifyResponse(valid=False)
        
        # Extract claims
        from uuid import UUID
        from datetime import datetime
        
        user_id = UUID(claims.get("sub")) if claims.get("sub") else None
        expires_at = datetime.fromtimestamp(claims.get("exp")) if claims.get("exp") else None
        
        return AccessTokenVerifyResponse(
            valid=True,
            user_id=user_id,
            user_type=claims.get("user_type"),
            tenant_id=UUID(claims.get("tenant_id")) if claims.get("tenant_id") else None,
            roles=claims.get("roles", []),
            expires_at=expires_at.isoformat() if expires_at else None,
        )
    except Exception:
        return AccessTokenVerifyResponse(valid=False)
