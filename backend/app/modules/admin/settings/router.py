from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.core.database import get_session
from app.modules.auth.dependencies import CurrentUser, get_current_user, require_permission
from app.modules.admin.settings.schemas import (
    SettingCreate,
    SettingListResponse,
    SettingOut,
    SettingUpdate,
    Pagination,
)
from app.modules.admin.settings.service import SettingsService


router = APIRouter()


@router.get(
    "/",
    response_model=SettingListResponse,
    dependencies=[Depends(require_permission("admin:settings:read"))],
)
async def list_settings(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
) -> SettingListResponse:
    service = SettingsService(session)
    items, total = await service.list(page, limit)
    return SettingListResponse(
        items=[SettingOut.model_validate(item) for item in items],
        pagination=Pagination(page=page, limit=limit, total=total),
    )


@router.get(
    "/{setting_id}",
    response_model=SettingOut,
    dependencies=[Depends(require_permission("admin:settings:read"))],
)
async def get_setting(setting_id: str, session: AsyncSession = Depends(get_session)) -> SettingOut:
    service = SettingsService(session)
    try:
        setting_uuid = UUID(setting_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid setting id") from exc

    setting = await service.get(setting_uuid)
    if not setting:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Setting not found")
    return SettingOut.model_validate(setting)


@router.post(
    "/",
    response_model=SettingOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("admin:settings:create"))],
)
async def create_setting(
    payload: SettingCreate,
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> SettingOut:
    service = SettingsService(session)
    try:
        setting = await service.create(payload, updated_by=current_user.id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return SettingOut.model_validate(setting)


@router.put(
    "/{setting_id}",
    response_model=SettingOut,
    dependencies=[Depends(require_permission("admin:settings:update"))],
)
async def update_setting(
    setting_id: str,
    payload: SettingUpdate,
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> SettingOut:
    service = SettingsService(session)
    try:
        setting_uuid = UUID(setting_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid setting id") from exc

    setting = await service.get(setting_uuid)
    if not setting:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Setting not found")

    updated = await service.update(setting, payload, updated_by=current_user.id)
    return SettingOut.model_validate(updated)


@router.delete(
    "/{setting_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_permission("admin:settings:delete"))],
)
async def delete_setting(
    setting_id: str, session: AsyncSession = Depends(get_session)
) -> None:
    service = SettingsService(session)
    try:
        setting_uuid = UUID(setting_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid setting id") from exc

    setting = await service.get(setting_uuid)
    if not setting:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Setting not found")

    await service.delete(setting)
    return None
