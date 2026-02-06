from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.modules.admin.dashboard.schemas import AdminDashboardSummaryOut
from app.modules.admin.dashboard.service import AdminDashboardService
from app.modules.auth.dependencies import require_permission


router = APIRouter()


@router.get(
    "/summary",
    response_model=AdminDashboardSummaryOut,
    dependencies=[Depends(require_permission("admin:dashboard:read"))],
)
async def get_dashboard_summary(
    session: AsyncSession = Depends(get_session),
) -> AdminDashboardSummaryOut:
    service = AdminDashboardService(session)
    summary = await service.get_summary()
    return AdminDashboardSummaryOut.model_validate(summary)
