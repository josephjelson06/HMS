from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.core.database import get_session
from app.modules.auth.dependencies import require_permission
from app.modules.admin.helpdesk.schemas import (
    HelpdeskCreate,
    HelpdeskListResponse,
    HelpdeskOut,
    HelpdeskUpdate,
    Pagination,
)
from app.modules.admin.helpdesk.service import HelpdeskService


router = APIRouter()


def build_out(ticket, tenant_name=None, assignee_email=None) -> HelpdeskOut:
    return HelpdeskOut.model_validate(ticket).model_copy(
        update={"tenant_name": tenant_name, "assignee_email": assignee_email}
    )


@router.get(
    "/",
    response_model=HelpdeskListResponse,
    dependencies=[Depends(require_permission("admin:helpdesk:read"))],
)
async def list_tickets(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    status_filter: str | None = Query(None, alias="status"),
    priority: str | None = Query(None),
    tenant_id: str | None = Query(None),
    session: AsyncSession = Depends(get_session),
) -> HelpdeskListResponse:
    service = HelpdeskService(session)
    tenant_uuid = None
    if tenant_id:
        try:
            tenant_uuid = UUID(tenant_id)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid tenant id") from exc

    items, total = await service.list(page, limit, status_filter, priority, tenant_uuid)
    return HelpdeskListResponse(
        items=[build_out(ticket, tenant_name, assignee_email) for ticket, tenant_name, assignee_email in items],
        pagination=Pagination(page=page, limit=limit, total=total),
    )


@router.get(
    "/{ticket_id}",
    response_model=HelpdeskOut,
    dependencies=[Depends(require_permission("admin:helpdesk:read"))],
)
async def get_ticket(ticket_id: str, session: AsyncSession = Depends(get_session)) -> HelpdeskOut:
    service = HelpdeskService(session)
    try:
        ticket_uuid = UUID(ticket_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid ticket id") from exc

    ticket = await service.get(ticket_uuid)
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")
    return build_out(ticket)


@router.post(
    "/",
    response_model=HelpdeskOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("admin:helpdesk:create"))],
)
async def create_ticket(
    payload: HelpdeskCreate, session: AsyncSession = Depends(get_session)
) -> HelpdeskOut:
    service = HelpdeskService(session)
    try:
        ticket = await service.create(payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return build_out(ticket)


@router.put(
    "/{ticket_id}",
    response_model=HelpdeskOut,
    dependencies=[Depends(require_permission("admin:helpdesk:update"))],
)
async def update_ticket(
    ticket_id: str,
    payload: HelpdeskUpdate,
    session: AsyncSession = Depends(get_session),
) -> HelpdeskOut:
    service = HelpdeskService(session)
    try:
        ticket_uuid = UUID(ticket_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid ticket id") from exc

    ticket = await service.get(ticket_uuid)
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")

    try:
        updated = await service.update(ticket, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return build_out(updated)


@router.delete(
    "/{ticket_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_permission("admin:helpdesk:delete"))],
)
async def delete_ticket(ticket_id: str, session: AsyncSession = Depends(get_session)) -> None:
    service = HelpdeskService(session)
    try:
        ticket_uuid = UUID(ticket_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid ticket id") from exc

    ticket = await service.get(ticket_uuid)
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")

    await service.delete(ticket)
    return None
