from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.modules.auth.dependencies import CurrentUser, get_current_user, require_permission
from app.modules.hotel.dashboard.schemas import HotelDashboardSummaryOut
from app.modules.hotel.dashboard.service import HotelDashboardService


router = APIRouter()


@router.get(
    "/summary",
    response_model=HotelDashboardSummaryOut,
    dependencies=[Depends(require_permission("hotel:dashboard:read"))],
)
async def get_dashboard_summary(
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> HotelDashboardSummaryOut:
    if current_user.tenant_id is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Tenant context missing")

    service = HotelDashboardService(session)
    summary = await service.get_summary(current_user.tenant_id)
    return HotelDashboardSummaryOut.model_validate(summary)
