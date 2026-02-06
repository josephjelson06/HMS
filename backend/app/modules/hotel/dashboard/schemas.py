from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class RecentIncidentOut(BaseModel):
    id: UUID
    title: str
    status: str
    severity: str
    occurred_at: datetime | None = None


class HotelDashboardSummaryOut(BaseModel):
    total_guests: int
    active_guests: int
    total_rooms: int
    occupied_rooms: int
    occupancy_rate: float
    open_incidents: int
    open_helpdesk_tickets: int
    active_kiosks: int
    outstanding_balance_cents: int
    recent_incidents: list[RecentIncidentOut]
