from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.core.database import get_session
from app.modules.auth.dependencies import require_permission
from app.modules.admin.audit.schemas import (
    AuditLogListResponse,
    AuditLogOut,
    Pagination,
)
from app.modules.admin.audit.service import AuditLogService


router = APIRouter()


@router.get(
    "/",
    response_model=AuditLogListResponse,
    dependencies=[Depends(require_permission("admin:audit:read"))],
)
async def list_audit_logs(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    user_id: str | None = Query(None),
    tenant_id: str | None = Query(None),
    action: str | None = Query(None),
    resource_type: str | None = Query(None),
    date_from: datetime | None = Query(None),
    date_to: datetime | None = Query(None),
    session: AsyncSession = Depends(get_session),
) -> AuditLogListResponse:
    service = AuditLogService(session)

    user_uuid = None
    tenant_uuid = None
    try:
        if user_id:
            user_uuid = UUID(user_id)
        if tenant_id:
            tenant_uuid = UUID(tenant_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid filter id"
        ) from exc

    items, total = await service.list_logs(
        page=page,
        limit=limit,
        user_id=user_uuid,
        tenant_id=tenant_uuid,
        action=action,
        resource_type=resource_type,
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
    dependencies=[Depends(require_permission("admin:audit:read"))],
)
async def get_audit_log(
    audit_id: str, session: AsyncSession = Depends(get_session)
) -> AuditLogOut:
    service = AuditLogService(session)
    try:
        audit_uuid = UUID(audit_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid audit id"
        ) from exc

    audit = await service.get(audit_uuid)
    if not audit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Audit log not found"
        )

    return AuditLogOut.model_validate(audit)
