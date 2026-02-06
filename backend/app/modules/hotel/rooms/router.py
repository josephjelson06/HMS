from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.core.database import get_session
from app.modules.auth.dependencies import CurrentUser, get_current_user, require_permission
from app.modules.hotel.rooms.schemas import (
    RoomCreate,
    RoomListResponse,
    RoomOut,
    RoomUpdate,
    Pagination,
)
from app.modules.hotel.rooms.service import RoomService


router = APIRouter()


@router.get(
    "/",
    response_model=RoomListResponse,
    dependencies=[Depends(require_permission("hotel:rooms:read"))],
)
async def list_rooms(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    search: str | None = Query(None),
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> RoomListResponse:
    if current_user.tenant_id is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Tenant context missing")
    service = RoomService(session)
    items, total = await service.list(current_user.tenant_id, page, limit, search)
    return RoomListResponse(
        items=[RoomOut.model_validate(item) for item in items],
        pagination=Pagination(page=page, limit=limit, total=total),
    )


@router.get(
    "/{room_id}",
    response_model=RoomOut,
    dependencies=[Depends(require_permission("hotel:rooms:read"))],
)
async def get_room(
    room_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> RoomOut:
    if current_user.tenant_id is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Tenant context missing")
    service = RoomService(session)
    try:
        room_uuid = UUID(room_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid room id") from exc

    room = await service.get(current_user.tenant_id, room_uuid)
    if not room:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Room not found")
    return RoomOut.model_validate(room)


@router.post(
    "/",
    response_model=RoomOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("hotel:rooms:create"))],
)
async def create_room(
    payload: RoomCreate,
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> RoomOut:
    if current_user.tenant_id is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Tenant context missing")
    service = RoomService(session)
    try:
        room = await service.create(current_user.tenant_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return RoomOut.model_validate(room)


@router.put(
    "/{room_id}",
    response_model=RoomOut,
    dependencies=[Depends(require_permission("hotel:rooms:update"))],
)
async def update_room(
    room_id: str,
    payload: RoomUpdate,
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> RoomOut:
    if current_user.tenant_id is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Tenant context missing")
    service = RoomService(session)
    try:
        room_uuid = UUID(room_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid room id") from exc

    room = await service.get(current_user.tenant_id, room_uuid)
    if not room:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Room not found")

    try:
        updated = await service.update(room, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return RoomOut.model_validate(updated)


@router.delete(
    "/{room_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_permission("hotel:rooms:delete"))],
)
async def delete_room(
    room_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> None:
    if current_user.tenant_id is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Tenant context missing")
    service = RoomService(session)
    try:
        room_uuid = UUID(room_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid room id") from exc

    room = await service.get(current_user.tenant_id, room_uuid)
    if not room:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Room not found")

    await service.delete(room)
    return None
