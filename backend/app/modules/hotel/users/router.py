from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.core.database import get_session
from app.modules.auth.dependencies import CurrentUser, get_current_user, require_permission
from app.modules.hotel.users.schemas import (
    HotelRoleOut,
    HotelUserCreate,
    HotelUserListResponse,
    HotelUserOut,
    HotelUserUpdate,
    Pagination,
)
from app.modules.hotel.users.service import HotelUserService


router = APIRouter()


@router.get(
    "/roles",
    response_model=list[HotelRoleOut],
    dependencies=[Depends(require_permission("hotel:users:read"))],
)
async def list_roles(
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> list[HotelRoleOut]:
    if current_user.tenant_id is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Tenant context missing")
    service = HotelUserService(session)
    roles = await service.list_roles(current_user.tenant_id)
    return [HotelRoleOut.model_validate(role) for role in roles]


@router.get(
    "/",
    response_model=HotelUserListResponse,
    dependencies=[Depends(require_permission("hotel:users:read"))],
)
async def list_users(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> HotelUserListResponse:
    if current_user.tenant_id is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Tenant context missing")
    service = HotelUserService(session)
    items, total = await service.list_users(current_user.tenant_id, page, limit)
    return HotelUserListResponse(
        items=[
            HotelUserOut.model_validate(user).model_copy(update={"roles": roles})
            for user, roles in items
        ],
        pagination=Pagination(page=page, limit=limit, total=total),
    )


@router.get(
    "/{user_id}",
    response_model=HotelUserOut,
    dependencies=[Depends(require_permission("hotel:users:read"))],
)
async def get_user(
    user_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> HotelUserOut:
    if current_user.tenant_id is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Tenant context missing")
    service = HotelUserService(session)
    try:
        user_uuid = UUID(user_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid user id") from exc

    user = await service.get(user_uuid)
    if not user or user.user_type != "hotel" or user.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    roles = await service.get_roles_for_user(user_uuid)
    return HotelUserOut.model_validate(user).model_copy(update={"roles": roles})


@router.post(
    "/",
    response_model=HotelUserOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("hotel:users:create"))],
)
async def create_user(
    payload: HotelUserCreate,
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> HotelUserOut:
    if current_user.tenant_id is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Tenant context missing")
    service = HotelUserService(session)
    try:
        user = await service.create(current_user.tenant_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    roles = await service.get_roles_for_user(user.id)
    return HotelUserOut.model_validate(user).model_copy(update={"roles": roles})


@router.put(
    "/{user_id}",
    response_model=HotelUserOut,
    dependencies=[Depends(require_permission("hotel:users:update"))],
)
async def update_user(
    user_id: str,
    payload: HotelUserUpdate,
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> HotelUserOut:
    if current_user.tenant_id is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Tenant context missing")
    service = HotelUserService(session)
    try:
        user_uuid = UUID(user_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid user id") from exc

    user = await service.get(user_uuid)
    if not user or user.user_type != "hotel" or user.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    try:
        updated = await service.update(user, current_user.tenant_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    roles = await service.get_roles_for_user(updated.id)
    return HotelUserOut.model_validate(updated).model_copy(update={"roles": roles})


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_permission("hotel:users:delete"))],
)
async def delete_user(
    user_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> None:
    if current_user.tenant_id is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Tenant context missing")
    service = HotelUserService(session)
    try:
        user_uuid = UUID(user_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid user id") from exc

    user = await service.get(user_uuid)
    if not user or user.user_type != "hotel" or user.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    await service.delete(user)
    return None
