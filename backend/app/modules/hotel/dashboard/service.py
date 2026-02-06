from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.guest import Guest
from app.models.helpdesk_ticket import HelpdeskTicket
from app.models.incident import Incident
from app.models.invoice import Invoice
from app.models.kiosk import Kiosk
from app.models.room import Room


class HotelDashboardService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_summary(self, tenant_id: UUID) -> dict[str, Any]:
        total_guests = await self.session.scalar(
            select(func.count()).select_from(Guest).where(Guest.tenant_id == tenant_id)
        )
        active_guests = await self.session.scalar(
            select(func.count())
            .select_from(Guest)
            .where(Guest.tenant_id == tenant_id, Guest.status == "active")
        )
        total_rooms = await self.session.scalar(
            select(func.count()).select_from(Room).where(Room.tenant_id == tenant_id)
        )
        occupied_rooms = await self.session.scalar(
            select(func.count())
            .select_from(Room)
            .where(Room.tenant_id == tenant_id, Room.status == "occupied")
        )
        open_incidents = await self.session.scalar(
            select(func.count())
            .select_from(Incident)
            .where(
                Incident.tenant_id == tenant_id,
                Incident.status.in_(["open", "in_progress"]),
            )
        )
        open_helpdesk = await self.session.scalar(
            select(func.count())
            .select_from(HelpdeskTicket)
            .where(
                HelpdeskTicket.tenant_id == tenant_id,
                HelpdeskTicket.status.in_(["open", "in_progress"]),
            )
        )
        active_kiosks = await self.session.scalar(
            select(func.count())
            .select_from(Kiosk)
            .where(Kiosk.tenant_id == tenant_id, Kiosk.status == "active")
        )
        outstanding_balance = await self.session.scalar(
            select(func.coalesce(func.sum(Invoice.amount_cents), 0))
            .select_from(Invoice)
            .where(Invoice.tenant_id == tenant_id, Invoice.status != "paid")
        )

        recent_incidents_result = await self.session.execute(
            select(Incident)
            .where(Incident.tenant_id == tenant_id)
            .order_by(Incident.occurred_at.desc().nullslast(), Incident.created_at.desc())
            .limit(5)
        )
        recent_incidents = recent_incidents_result.scalars().all()

        rooms_total = int(total_rooms or 0)
        rooms_occupied = int(occupied_rooms or 0)
        occupancy_rate = (rooms_occupied / rooms_total * 100.0) if rooms_total > 0 else 0.0

        return {
            "total_guests": int(total_guests or 0),
            "active_guests": int(active_guests or 0),
            "total_rooms": rooms_total,
            "occupied_rooms": rooms_occupied,
            "occupancy_rate": round(occupancy_rate, 2),
            "open_incidents": int(open_incidents or 0),
            "open_helpdesk_tickets": int(open_helpdesk or 0),
            "active_kiosks": int(active_kiosks or 0),
            "outstanding_balance_cents": int(outstanding_balance or 0),
            "recent_incidents": [
                {
                    "id": incident.id,
                    "title": incident.title,
                    "status": incident.status,
                    "severity": incident.severity,
                    "occurred_at": incident.occurred_at,
                }
                for incident in recent_incidents
            ],
        }
