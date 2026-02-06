from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.core.database import get_session
from app.modules.auth.dependencies import CurrentUser, get_current_user, require_permission
from app.modules.hotel.roles.schemas import PermissionOut, RoleCreate, RoleOut, RoleUpdate
from app.modules.hotel.roles.service import HotelRoleService


router = APIRouter()


@router.get(
    "/permissions",
    response_model=list[PermissionOut],
    dependencies=[Depends(require_permission("hotel:roles:read"))],
)
async def list_permissions(
    session: AsyncSession = Depends(get_session),
) -> list[PermissionOut]:
    service = HotelRoleService(session)
    permissions = await service.list_permissions()
    return [PermissionOut.model_validate(permission) for permission in permissions]


@router.get(
    "/",
    response_model=list[RoleOut],
    dependencies=[Depends(require_permission("hotel:roles:read"))],
)
async def list_roles(
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> list[RoleOut]:
    if current_user.tenant_id is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Tenant context missing")
    service = HotelRoleService(session)
    roles = await service.list_roles(current_user.tenant_id)
    return [
        RoleOut.model_validate(role).model_copy(update={"permissions": perms})
        for role, perms in roles
    ]


@router.get(
    "/{role_id}",
    response_model=RoleOut,
    dependencies=[Depends(require_permission("hotel:roles:read"))],
)
async def get_role(
    role_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> RoleOut:
    if current_user.tenant_id is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Tenant context missing")
    service = HotelRoleService(session)
    try:
        role_uuid = UUID(role_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid role id") from exc

    role = await service.get(role_uuid)
    if (
        not role
        or role.role_type != "hotel"
        or (role.tenant_id is not None and role.tenant_id != current_user.tenant_id)
    ):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")

    perms = await service.get_permissions_for_role(role_uuid)
    return RoleOut.model_validate(role).model_copy(update={"permissions": perms})


@router.post(
    "/",
    response_model=RoleOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("hotel:roles:create"))],
)
async def create_role(
    payload: RoleCreate,
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> RoleOut:
    if current_user.tenant_id is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Tenant context missing")
    service = HotelRoleService(session)
    try:
        role = await service.create(current_user.tenant_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    perms = await service.get_permissions_for_role(role.id)
    return RoleOut.model_validate(role).model_copy(update={"permissions": perms})


@router.put(
    "/{role_id}",
    response_model=RoleOut,
    dependencies=[Depends(require_permission("hotel:roles:update"))],
)
async def update_role(
    role_id: str,
    payload: RoleUpdate,
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> RoleOut:
    if current_user.tenant_id is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Tenant context missing")
    service = HotelRoleService(session)
    try:
        role_uuid = UUID(role_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid role id") from exc

    role = await service.get(role_uuid)
    if (
        not role
        or role.role_type != "hotel"
        or (role.tenant_id is not None and role.tenant_id != current_user.tenant_id)
    ):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")

    try:
        updated = await service.update(role, current_user.tenant_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    perms = await service.get_permissions_for_role(updated.id)
    return RoleOut.model_validate(updated).model_copy(update={"permissions": perms})


@router.delete(
    "/{role_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_permission("hotel:roles:delete"))],
)
async def delete_role(
    role_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> None:
    if current_user.tenant_id is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Tenant context missing")
    service = HotelRoleService(session)
    try:
        role_uuid = UUID(role_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid role id") from exc

    role = await service.get(role_uuid)
    if (
        not role
        or role.role_type != "hotel"
        or (role.tenant_id is not None and role.tenant_id != current_user.tenant_id)
    ):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")

    try:
        await service.delete(role, current_user.tenant_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return None
