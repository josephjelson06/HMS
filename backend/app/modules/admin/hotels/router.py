from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.core.database import get_session
from app.modules.auth.dependencies import require_permission
from app.modules.admin.hotels.schemas import (
    HotelCreate,
    HotelListResponse,
    HotelOut,
    HotelUpdate,
    Pagination,
)
from app.modules.admin.hotels.service import HotelService


router = APIRouter()


@router.get(
    "/",
    response_model=HotelListResponse,
    dependencies=[Depends(require_permission("admin:hotels:read"))],
)
async def list_hotels(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
) -> HotelListResponse:
    service = HotelService(session)
    items, total = await service.list_hotels(page, limit)
    return HotelListResponse(
        items=[HotelOut.model_validate(item) for item in items],
        pagination=Pagination(page=page, limit=limit, total=total),
    )


@router.get(
    "/{tenant_id}",
    response_model=HotelOut,
    dependencies=[Depends(require_permission("admin:hotels:read"))],
)
async def get_hotel(
    tenant_id: str,
    session: AsyncSession = Depends(get_session),
) -> HotelOut:
    service = HotelService(session)
    try:
        tenant_uuid = UUID(tenant_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid hotel id"
        ) from exc

    tenant = await service.get(tenant_uuid)
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Hotel not found"
        )
    return HotelOut.model_validate(tenant)


@router.post(
    "/",
    response_model=HotelOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("admin:hotels:create"))],
)
async def create_hotel(
    payload: HotelCreate,
    session: AsyncSession = Depends(get_session),
) -> HotelOut:
    service = HotelService(session)
    try:
        tenant = await service.create(payload)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc
    return HotelOut.model_validate(tenant)


@router.put(
    "/{tenant_id}",
    response_model=HotelOut,
    dependencies=[Depends(require_permission("admin:hotels:update"))],
)
async def update_hotel(
    tenant_id: str,
    payload: HotelUpdate,
    session: AsyncSession = Depends(get_session),
) -> HotelOut:
    service = HotelService(session)
    try:
        tenant_uuid = UUID(tenant_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid hotel id"
        ) from exc

    tenant = await service.get(tenant_uuid)
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Hotel not found"
        )
    try:
        updated = await service.update(tenant, payload)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc
    return HotelOut.model_validate(updated)


@router.delete(
    "/{tenant_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_permission("admin:hotels:delete"))],
)
async def delete_hotel(
    tenant_id: str,
    session: AsyncSession = Depends(get_session),
) -> None:
    service = HotelService(session)
    try:
        tenant_uuid = UUID(tenant_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid hotel id"
        ) from exc

    tenant = await service.get(tenant_uuid)
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Hotel not found"
        )
    await service.delete(tenant)
    return None
