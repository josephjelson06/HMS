from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class RecentHotelOut(BaseModel):
    id: UUID
    name: str
    status: str
    created_at: datetime | None = None


class AdminDashboardSummaryOut(BaseModel):
    total_hotels: int
    active_hotels: int
    active_subscriptions: int
    open_helpdesk_tickets: int
    monthly_revenue_cents: int
    outstanding_balance_cents: int
    new_hotels_last_30_days: int
    recent_hotels: list[RecentHotelOut]
