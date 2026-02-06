from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.core.database import get_session
from app.modules.auth.dependencies import CurrentUser, get_current_user, require_permission
from app.modules.hotel.audit.schemas import AuditLogListResponse, AuditLogOut, Pagination
from app.modules.hotel.audit.service import HotelAuditLogService


router = APIRouter()


@router.get(
    "/",
    response_model=AuditLogListResponse,
    dependencies=[Depends(require_permission("hotel:audit:read"))],
)
async def list_audit_logs(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    action: str | None = Query(None),
    user_id: str | None = Query(None),
    date_from: datetime | None = Query(None),
    date_to: datetime | None = Query(None),
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> AuditLogListResponse:
    if current_user.tenant_id is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Tenant context missing")
    service = HotelAuditLogService(session)

    user_uuid = None
    if user_id:
        try:
            user_uuid = UUID(user_id)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid user id") from exc

    items, total = await service.list_logs(
        tenant_id=current_user.tenant_id,
        page=page,
        limit=limit,
        action=action,
        user_id=user_uuid,
        date_from=date_from,
        date_to=date_to,
    )
    return AuditLogListResponse(
        items=[AuditLogOut.model_validate(item) for item in items],
        pagination=Pagination(page=page, limit=limit, total=total),
    )


@router.get(
    "/{audit_id}",
    response_model=AuditLogOut,
    dependencies=[Depends(require_permission("hotel:audit:read"))],
)
async def get_audit_log(
    audit_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> AuditLogOut:
    if current_user.tenant_id is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Tenant context missing")
    service = HotelAuditLogService(session)
    try:
        audit_uuid = UUID(audit_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid audit id") from exc

    audit = await service.get(current_user.tenant_id, audit_uuid)
    if not audit:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Audit log not found")
    return AuditLogOut.model_validate(audit)
