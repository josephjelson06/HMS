from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_session
from app.models.tenant import Tenant
from app.modules.auth.dependencies import CurrentUser, get_current_user, require_permission
from app.modules.auth.schemas import (
    AuthResponse,
    ImpersonationStartRequest,
    LoginRequest,
    LogoutResponse,
    TenantOut,
    UserOut,
)
from app.modules.auth.service import AuthService


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
    try:
        result = await service.refresh(refresh_token)
    except HTTPException as exc:
        # If reuse is detected, clear cookies to force re-login
        if "reuse detected" in str(exc.detail).lower():
            clear_auth_cookies(response)
        raise
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
