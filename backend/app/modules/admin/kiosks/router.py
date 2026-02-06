from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.core.database import get_session
from app.modules.auth.dependencies import require_permission
from app.modules.admin.kiosks.schemas import (
    KioskCreate,
    KioskListResponse,
    KioskOut,
    KioskUpdate,
    Pagination,
)
from app.modules.admin.kiosks.service import KioskService


router = APIRouter()


def build_out(kiosk, tenant_name=None, issued_token: str | None = None) -> KioskOut:
    return KioskOut.model_validate(kiosk).model_copy(
        update={
            "tenant_name": tenant_name,
            "issued_token": issued_token,
        }
    )


@router.get(
    "/",
    response_model=KioskListResponse,
    dependencies=[Depends(require_permission("admin:kiosks:read"))],
)
async def list_kiosks(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
) -> KioskListResponse:
    service = KioskService(session)
    items, total = await service.list(page, limit)
    return KioskListResponse(
        items=[build_out(kiosk, tenant_name) for kiosk, tenant_name in items],
        pagination=Pagination(page=page, limit=limit, total=total),
    )


@router.get(
    "/{kiosk_id}",
    response_model=KioskOut,
    dependencies=[Depends(require_permission("admin:kiosks:read"))],
)
async def get_kiosk(
    kiosk_id: str, session: AsyncSession = Depends(get_session)
) -> KioskOut:
    service = KioskService(session)
    try:
        kiosk_uuid = UUID(kiosk_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid kiosk id") from exc

    kiosk = await service.get(kiosk_uuid)
    if not kiosk:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Kiosk not found")
    return build_out(kiosk)


@router.post(
    "/",
    response_model=KioskOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("admin:kiosks:create"))],
)
async def create_kiosk(
    payload: KioskCreate, session: AsyncSession = Depends(get_session)
) -> KioskOut:
    service = KioskService(session)
    try:
        kiosk, token = await service.create(payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return build_out(kiosk, issued_token=token)


@router.put(
    "/{kiosk_id}",
    response_model=KioskOut,
    dependencies=[Depends(require_permission("admin:kiosks:update"))],
)
async def update_kiosk(
    kiosk_id: str,
    payload: KioskUpdate,
    session: AsyncSession = Depends(get_session),
) -> KioskOut:
    service = KioskService(session)
    try:
        kiosk_uuid = UUID(kiosk_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid kiosk id") from exc

    kiosk = await service.get(kiosk_uuid)
    if not kiosk:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Kiosk not found")

    try:
        updated, issued_token = await service.update(kiosk, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return build_out(updated, issued_token=issued_token)


@router.delete(
    "/{kiosk_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_permission("admin:kiosks:delete"))],
)
async def delete_kiosk(
    kiosk_id: str, session: AsyncSession = Depends(get_session)
) -> None:
    service = KioskService(session)
    try:
        kiosk_uuid = UUID(kiosk_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid kiosk id") from exc

    kiosk = await service.get(kiosk_uuid)
    if not kiosk:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Kiosk not found")
    await service.delete(kiosk)
    return None
