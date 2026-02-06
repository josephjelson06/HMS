from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.modules.auth.dependencies import CurrentUser, get_current_user, require_permission
from app.modules.hotel.helpdesk.schemas import HelpdeskCreate, HelpdeskOut
from app.modules.hotel.helpdesk.service import HotelHelpdeskService


router = APIRouter()


@router.get(
    "/",
    response_model=list[HelpdeskOut],
    dependencies=[Depends(require_permission("hotel:support:read"))],
)
async def list_tickets(
    limit: int = Query(20, ge=1, le=100),
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> list[HelpdeskOut]:
    if current_user.tenant_id is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Tenant context missing")
    service = HotelHelpdeskService(session)
    tickets = await service.list(current_user.tenant_id, limit)
    return [HelpdeskOut.model_validate(ticket) for ticket in tickets]


@router.post(
    "/",
    response_model=HelpdeskOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("hotel:support:create"))],
)
async def create_ticket(
    payload: HelpdeskCreate,
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> HelpdeskOut:
    if current_user.tenant_id is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Tenant context missing")
    service = HotelHelpdeskService(session)
    ticket = await service.create(current_user.tenant_id, payload)
    return HelpdeskOut.model_validate(ticket)
