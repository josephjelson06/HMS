from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.core.database import get_session
from app.modules.auth.dependencies import CurrentUser, get_current_user, require_permission
from app.modules.hotel.incidents.schemas import (
    IncidentCreate,
    IncidentListResponse,
    IncidentOut,
    IncidentUpdate,
    Pagination,
)
from app.modules.hotel.incidents.service import IncidentService


router = APIRouter()


@router.get(
    "/",
    response_model=IncidentListResponse,
    dependencies=[Depends(require_permission("hotel:incidents:read"))],
)
async def list_incidents(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    search: str | None = Query(None),
    status_filter: str | None = Query(None, alias="status"),
    severity: str | None = Query(None),
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> IncidentListResponse:
    if current_user.tenant_id is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Tenant context missing")
    service = IncidentService(session)
    items, total = await service.list(
        current_user.tenant_id, page, limit, search, status_filter, severity
    )
    return IncidentListResponse(
        items=[IncidentOut.model_validate(item) for item in items],
        pagination=Pagination(page=page, limit=limit, total=total),
    )


@router.get(
    "/{incident_id}",
    response_model=IncidentOut,
    dependencies=[Depends(require_permission("hotel:incidents:read"))],
)
async def get_incident(
    incident_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> IncidentOut:
    if current_user.tenant_id is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Tenant context missing")
    service = IncidentService(session)
    try:
        incident_uuid = UUID(incident_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid incident id") from exc

    incident = await service.get(current_user.tenant_id, incident_uuid)
    if not incident:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")
    return IncidentOut.model_validate(incident)


@router.post(
    "/",
    response_model=IncidentOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("hotel:incidents:create"))],
)
async def create_incident(
    payload: IncidentCreate,
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> IncidentOut:
    if current_user.tenant_id is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Tenant context missing")
    service = IncidentService(session)
    try:
        incident = await service.create(current_user.tenant_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return IncidentOut.model_validate(incident)


@router.put(
    "/{incident_id}",
    response_model=IncidentOut,
    dependencies=[Depends(require_permission("hotel:incidents:update"))],
)
async def update_incident(
    incident_id: str,
    payload: IncidentUpdate,
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> IncidentOut:
    if current_user.tenant_id is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Tenant context missing")
    service = IncidentService(session)
    try:
        incident_uuid = UUID(incident_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid incident id") from exc

    incident = await service.get(current_user.tenant_id, incident_uuid)
    if not incident:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")

    try:
        updated = await service.update(incident, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return IncidentOut.model_validate(updated)


@router.delete(
    "/{incident_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_permission("hotel:incidents:delete"))],
)
async def delete_incident(
    incident_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> None:
    if current_user.tenant_id is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Tenant context missing")
    service = IncidentService(session)
    try:
        incident_uuid = UUID(incident_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid incident id") from exc

    incident = await service.get(current_user.tenant_id, incident_uuid)
    if not incident:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")

    await service.delete(incident)
    return None
