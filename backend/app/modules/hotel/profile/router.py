from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.modules.auth.dependencies import CurrentUser, get_current_user, require_permission
from app.modules.hotel.profile.schemas import ProfileOut, ProfileUpdate
from app.modules.hotel.profile.service import ProfileService


router = APIRouter()


@router.get(
    "/",
    response_model=ProfileOut,
    dependencies=[Depends(require_permission("hotel:profile:read"))],
)
async def get_profile(
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ProfileOut:
    if current_user.tenant_id is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Tenant context missing")
    service = ProfileService(session)
    user = await service.get(current_user.id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return ProfileOut.model_validate(user)


@router.put(
    "/",
    response_model=ProfileOut,
    dependencies=[Depends(require_permission("hotel:profile:update"))],
)
async def update_profile(
    payload: ProfileUpdate,
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ProfileOut:
    if current_user.tenant_id is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Tenant context missing")
    service = ProfileService(session)
    user = await service.get(current_user.id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    try:
        updated = await service.update(user, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return ProfileOut.model_validate(updated)
