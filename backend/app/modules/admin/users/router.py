from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.core.database import get_session
from app.modules.auth.dependencies import require_permission
from app.modules.admin.users.schemas import (
    AdminRoleOut,
    AdminUserCreate,
    AdminUserListResponse,
    AdminUserOut,
    AdminUserUpdate,
    Pagination,
)
from app.modules.admin.users.service import AdminUserService


router = APIRouter()


@router.get(
    "/roles",
    response_model=list[AdminRoleOut],
    dependencies=[Depends(require_permission("admin:users:read"))],
)
async def list_roles(
    session: AsyncSession = Depends(get_session),
) -> list[AdminRoleOut]:
    service = AdminUserService(session)
    roles = await service.list_roles()
    return [AdminRoleOut.model_validate(role) for role in roles]


@router.get(
    "/",
    response_model=AdminUserListResponse,
    dependencies=[Depends(require_permission("admin:users:read"))],
)
async def list_users(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
) -> AdminUserListResponse:
    service = AdminUserService(session)
    items, total = await service.list_users(page, limit)
    return AdminUserListResponse(
        items=[
            AdminUserOut.model_validate(user).model_copy(update={"roles": roles})
            for user, roles in items
        ],
        pagination=Pagination(page=page, limit=limit, total=total),
    )


@router.get(
    "/{user_id}",
    response_model=AdminUserOut,
    dependencies=[Depends(require_permission("admin:users:read"))],
)
async def get_user(
    user_id: str,
    session: AsyncSession = Depends(get_session),
) -> AdminUserOut:
    service = AdminUserService(session)
    try:
        user_uuid = UUID(user_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid user id"
        ) from exc

    user = await service.get(user_uuid)
    if not user or user.user_type != "platform":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    roles = await service.get_roles_for_user(user_uuid)
    return AdminUserOut.model_validate(user).model_copy(update={"roles": roles})


@router.post(
    "/",
    response_model=AdminUserOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("admin:users:create"))],
)
async def create_user(
    payload: AdminUserCreate,
    session: AsyncSession = Depends(get_session),
) -> AdminUserOut:
    service = AdminUserService(session)
    try:
        user = await service.create(payload)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc

    roles = await service.get_roles_for_user(user.id)
    return AdminUserOut.model_validate(user).model_copy(update={"roles": roles})


@router.put(
    "/{user_id}",
    response_model=AdminUserOut,
    dependencies=[Depends(require_permission("admin:users:update"))],
)
async def update_user(
    user_id: str,
    payload: AdminUserUpdate,
    session: AsyncSession = Depends(get_session),
) -> AdminUserOut:
    service = AdminUserService(session)
    try:
        user_uuid = UUID(user_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid user id"
        ) from exc

    user = await service.get(user_uuid)
    if not user or user.user_type != "platform":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    try:
        updated = await service.update(user, payload)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc

    roles = await service.get_roles_for_user(updated.id)
    return AdminUserOut.model_validate(updated).model_copy(update={"roles": roles})


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_permission("admin:users:delete"))],
)
async def delete_user(
    user_id: str,
    session: AsyncSession = Depends(get_session),
) -> None:
    service = AdminUserService(session)
    try:
        user_uuid = UUID(user_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid user id"
        ) from exc

    user = await service.get(user_uuid)
    if not user or user.user_type != "platform":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    await service.delete(user)
    return None
