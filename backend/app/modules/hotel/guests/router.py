from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.core.database import get_session
from app.modules.auth.dependencies import CurrentUser, get_current_user, require_permission
from app.modules.hotel.guests.schemas import (
    GuestCreate,
    GuestListResponse,
    GuestOut,
    GuestUpdate,
    Pagination,
)
from app.modules.hotel.guests.service import GuestService


router = APIRouter()


@router.get(
    "/",
    response_model=GuestListResponse,
    dependencies=[Depends(require_permission("hotel:guests:read"))],
)
async def list_guests(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    search: str | None = Query(None),
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> GuestListResponse:
    if current_user.tenant_id is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Tenant context missing")
    service = GuestService(session)
    items, total = await service.list(current_user.tenant_id, page, limit, search)
    return GuestListResponse(
        items=[GuestOut.model_validate(item) for item in items],
        pagination=Pagination(page=page, limit=limit, total=total),
    )


@router.get(
    "/{guest_id}",
    response_model=GuestOut,
    dependencies=[Depends(require_permission("hotel:guests:read"))],
)
async def get_guest(
    guest_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> GuestOut:
    if current_user.tenant_id is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Tenant context missing")
    service = GuestService(session)
    try:
        guest_uuid = UUID(guest_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid guest id") from exc

    guest = await service.get(current_user.tenant_id, guest_uuid)
    if not guest:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Guest not found")
    return GuestOut.model_validate(guest)


@router.post(
    "/",
    response_model=GuestOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("hotel:guests:create"))],
)
async def create_guest(
    payload: GuestCreate,
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> GuestOut:
    if current_user.tenant_id is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Tenant context missing")
    service = GuestService(session)
    try:
        guest = await service.create(current_user.tenant_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return GuestOut.model_validate(guest)


@router.put(
    "/{guest_id}",
    response_model=GuestOut,
    dependencies=[Depends(require_permission("hotel:guests:update"))],
)
async def update_guest(
    guest_id: str,
    payload: GuestUpdate,
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> GuestOut:
    if current_user.tenant_id is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Tenant context missing")
    service = GuestService(session)
    try:
        guest_uuid = UUID(guest_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid guest id") from exc

    guest = await service.get(current_user.tenant_id, guest_uuid)
    if not guest:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Guest not found")

    try:
        updated = await service.update(guest, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return GuestOut.model_validate(updated)


@router.delete(
    "/{guest_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_permission("hotel:guests:delete"))],
)
async def delete_guest(
    guest_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> None:
    if current_user.tenant_id is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Tenant context missing")
    service = GuestService(session)
    try:
        guest_uuid = UUID(guest_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid guest id") from exc

    guest = await service.get(current_user.tenant_id, guest_uuid)
    if not guest:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Guest not found")

    await service.delete(guest)
    return None
