from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.core.database import get_session
from app.modules.auth.dependencies import CurrentUser, get_current_user, require_permission
from app.modules.hotel.kiosk_settings.schemas import (
    KioskSettingCreate,
    KioskSettingListResponse,
    KioskSettingOut,
    KioskSettingUpdate,
    Pagination,
)
from app.modules.hotel.kiosk_settings.service import KioskSettingsService


router = APIRouter()


def build_out(kiosk, issued_token: str | None = None) -> KioskSettingOut:
    return KioskSettingOut.model_validate(kiosk).model_copy(update={"issued_token": issued_token})


@router.get(
    "/",
    response_model=KioskSettingListResponse,
    dependencies=[Depends(require_permission("hotel:kiosks:read"))],
)
async def list_kiosks(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> KioskSettingListResponse:
    if current_user.tenant_id is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Tenant context missing")
    service = KioskSettingsService(session)
    items, total = await service.list(current_user.tenant_id, page, limit)
    return KioskSettingListResponse(
        items=[build_out(item) for item in items],
        pagination=Pagination(page=page, limit=limit, total=total),
    )


@router.get(
    "/{kiosk_id}",
    response_model=KioskSettingOut,
    dependencies=[Depends(require_permission("hotel:kiosks:read"))],
)
async def get_kiosk(
    kiosk_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> KioskSettingOut:
    if current_user.tenant_id is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Tenant context missing")
    service = KioskSettingsService(session)
    try:
        kiosk_uuid = UUID(kiosk_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid kiosk id") from exc

    kiosk = await service.get(current_user.tenant_id, kiosk_uuid)
    if not kiosk:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Kiosk not found")
    return build_out(kiosk)


@router.post(
    "/",
    response_model=KioskSettingOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("hotel:kiosks:create"))],
)
async def create_kiosk(
    payload: KioskSettingCreate,
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> KioskSettingOut:
    if current_user.tenant_id is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Tenant context missing")
    service = KioskSettingsService(session)
    try:
        kiosk, token = await service.create(current_user.tenant_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return build_out(kiosk, issued_token=token)


@router.put(
    "/{kiosk_id}",
    response_model=KioskSettingOut,
    dependencies=[Depends(require_permission("hotel:kiosks:update"))],
)
async def update_kiosk(
    kiosk_id: str,
    payload: KioskSettingUpdate,
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> KioskSettingOut:
    if current_user.tenant_id is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Tenant context missing")
    service = KioskSettingsService(session)
    try:
        kiosk_uuid = UUID(kiosk_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid kiosk id") from exc

    kiosk = await service.get(current_user.tenant_id, kiosk_uuid)
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
    dependencies=[Depends(require_permission("hotel:kiosks:delete"))],
)
async def delete_kiosk(
    kiosk_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> None:
    if current_user.tenant_id is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Tenant context missing")
    service = KioskSettingsService(session)
    try:
        kiosk_uuid = UUID(kiosk_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid kiosk id") from exc

    kiosk = await service.get(current_user.tenant_id, kiosk_uuid)
    if not kiosk:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Kiosk not found")
    await service.delete(kiosk)
    return None
