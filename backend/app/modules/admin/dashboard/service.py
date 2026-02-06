from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.helpdesk_ticket import HelpdeskTicket
from app.models.invoice import Invoice
from app.models.subscription import Subscription
from app.models.tenant import Tenant


class AdminDashboardService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_summary(self) -> dict[str, Any]:
        total_hotels = await self.session.scalar(select(func.count()).select_from(Tenant))
        active_hotels = await self.session.scalar(
            select(func.count()).select_from(Tenant).where(Tenant.status == "active")
        )
        active_subscriptions = await self.session.scalar(
            select(func.count()).select_from(Subscription).where(Subscription.status == "active")
        )

        open_helpdesk = await self.session.scalar(
            select(func.count()).select_from(HelpdeskTicket).where(
                HelpdeskTicket.status.in_(["open", "in_progress"])
            )
        )

        now = datetime.now(timezone.utc)
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        monthly_revenue = await self.session.scalar(
            select(func.coalesce(func.sum(Invoice.amount_cents), 0))
            .select_from(Invoice)
            .where(
                Invoice.status == "paid",
                Invoice.paid_at.is_not(None),
                Invoice.paid_at >= month_start,
            )
        )
        outstanding_balance = await self.session.scalar(
            select(func.coalesce(func.sum(Invoice.amount_cents), 0))
            .select_from(Invoice)
            .where(Invoice.status != "paid")
        )
        new_hotels = await self.session.scalar(
            select(func.count())
            .select_from(Tenant)
            .where(Tenant.created_at >= now - timedelta(days=30))
        )

        recent_hotels_result = await self.session.execute(
            select(Tenant).order_by(Tenant.created_at.desc()).limit(5)
        )
        recent_hotels = recent_hotels_result.scalars().all()

        return {
            "total_hotels": int(total_hotels or 0),
            "active_hotels": int(active_hotels or 0),
            "active_subscriptions": int(active_subscriptions or 0),
            "open_helpdesk_tickets": int(open_helpdesk or 0),
            "monthly_revenue_cents": int(monthly_revenue or 0),
            "outstanding_balance_cents": int(outstanding_balance or 0),
            "new_hotels_last_30_days": int(new_hotels or 0),
            "recent_hotels": [
                {
                    "id": hotel.id,
                    "name": hotel.name,
                    "status": hotel.status,
                    "created_at": hotel.created_at,
                }
                for hotel in recent_hotels
            ],
        }
