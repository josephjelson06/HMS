from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.storage import ReportStorage
from app.models.guest import Guest
from app.models.incident import Incident
from app.models.invoice import Invoice
from app.models.kiosk import Kiosk
from app.models.report_export import ReportExport
from app.models.room import Room


@dataclass(frozen=True)
class ReportDefinition:
    code: str
    title: str
    description: str


REPORT_DEFINITIONS = {
    "guest_activity": ReportDefinition(
        code="guest_activity",
        title="Guest Activity",
        description="Check-in activity and guest statuses over time.",
    ),
    "room_status": ReportDefinition(
        code="room_status",
        title="Room Status",
        description="Availability and room inventory breakdowns.",
    ),
    "incident_overview": ReportDefinition(
        code="incident_overview",
        title="Incident Overview",
        description="Incident volumes, severity trends, and resolution rates.",
    ),
    "kiosk_health": ReportDefinition(
        code="kiosk_health",
        title="Kiosk Health",
        description="Fleet status, connectivity, and last-seen activity.",
    ),
    "billing_snapshot": ReportDefinition(
        code="billing_snapshot",
        title="Billing Snapshot",
        description="Invoice activity and outstanding balances.",
    ),
}


def apply_date_filter(stmt, column, date_from: datetime | None, date_to: datetime | None):
    if date_from:
        stmt = stmt.where(column >= date_from)
    if date_to:
        stmt = stmt.where(column <= date_to)
    return stmt


class HotelReportService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.storage = ReportStorage(settings.reports_storage_path)

    async def list_reports(
        self,
        tenant_id: UUID,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
    ) -> list[dict[str, Any]]:
        guest_metrics = await self._guest_metrics(tenant_id, date_from, date_to)
        room_metrics = await self._room_metrics(tenant_id, date_from, date_to)
        incident_metrics = await self._incident_metrics(tenant_id, date_from, date_to)
        kiosk_metrics = await self._kiosk_metrics(tenant_id, date_from, date_to)
        billing_metrics = await self._billing_metrics(tenant_id, date_from, date_to)

        return [
            {
                "code": REPORT_DEFINITIONS["guest_activity"].code,
                "title": REPORT_DEFINITIONS["guest_activity"].title,
                "description": REPORT_DEFINITIONS["guest_activity"].description,
                "metrics": guest_metrics,
            },
            {
                "code": REPORT_DEFINITIONS["room_status"].code,
                "title": REPORT_DEFINITIONS["room_status"].title,
                "description": REPORT_DEFINITIONS["room_status"].description,
                "metrics": room_metrics,
            },
            {
                "code": REPORT_DEFINITIONS["incident_overview"].code,
                "title": REPORT_DEFINITIONS["incident_overview"].title,
                "description": REPORT_DEFINITIONS["incident_overview"].description,
                "metrics": incident_metrics,
            },
            {
                "code": REPORT_DEFINITIONS["kiosk_health"].code,
                "title": REPORT_DEFINITIONS["kiosk_health"].title,
                "description": REPORT_DEFINITIONS["kiosk_health"].description,
                "metrics": kiosk_metrics,
            },
            {
                "code": REPORT_DEFINITIONS["billing_snapshot"].code,
                "title": REPORT_DEFINITIONS["billing_snapshot"].title,
                "description": REPORT_DEFINITIONS["billing_snapshot"].description,
                "metrics": billing_metrics,
            },
        ]

    async def get_report(
        self,
        tenant_id: UUID,
        report_code: str,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        status: str | None = None,
    ) -> dict[str, Any]:
        definition = REPORT_DEFINITIONS.get(report_code)
        if not definition:
            raise ValueError("Unknown report")

        filters = {
            "date_from": date_from.isoformat() if date_from else None,
            "date_to": date_to.isoformat() if date_to else None,
            "status": status,
        }

        if report_code == "guest_activity":
            summary = await self._guest_metrics(tenant_id, date_from, date_to)
            rows = await self._guest_rows(tenant_id, date_from, date_to, status)
            columns = [
                {"key": "guest", "label": "Guest"},
                {"key": "status", "label": "Status"},
                {"key": "check_in_at", "label": "Check In"},
                {"key": "check_out_at", "label": "Check Out"},
                {"key": "email", "label": "Email"},
            ]
            return {
                "code": definition.code,
                "title": definition.title,
                "description": definition.description,
                "filters": filters,
                "summary": summary,
                "columns": columns,
                "rows": rows,
            }

        if report_code == "room_status":
            summary = await self._room_metrics(tenant_id, date_from, date_to)
            rows = await self._room_rows(tenant_id, date_from, date_to, status)
            columns = [
                {"key": "room_number", "label": "Room"},
                {"key": "room_type", "label": "Type"},
                {"key": "status", "label": "Status"},
                {"key": "floor", "label": "Floor"},
                {"key": "rate_cents", "label": "Rate (cents)"},
            ]
            return {
                "code": definition.code,
                "title": definition.title,
                "description": definition.description,
                "filters": filters,
                "summary": summary,
                "columns": columns,
                "rows": rows,
            }

        if report_code == "incident_overview":
            summary = await self._incident_metrics(tenant_id, date_from, date_to)
            rows = await self._incident_rows(tenant_id, date_from, date_to, status)
            columns = [
                {"key": "title", "label": "Incident"},
                {"key": "status", "label": "Status"},
                {"key": "severity", "label": "Severity"},
                {"key": "occurred_at", "label": "Occurred"},
                {"key": "resolved_at", "label": "Resolved"},
            ]
            return {
                "code": definition.code,
                "title": definition.title,
                "description": definition.description,
                "filters": filters,
                "summary": summary,
                "columns": columns,
                "rows": rows,
            }

        if report_code == "kiosk_health":
            summary = await self._kiosk_metrics(tenant_id, date_from, date_to)
            rows = await self._kiosk_rows(tenant_id, date_from, date_to, status)
            columns = [
                {"key": "name", "label": "Kiosk"},
                {"key": "location", "label": "Location"},
                {"key": "status", "label": "Status"},
                {"key": "last_seen_at", "label": "Last Seen"},
            ]
            return {
                "code": definition.code,
                "title": definition.title,
                "description": definition.description,
                "filters": filters,
                "summary": summary,
                "columns": columns,
                "rows": rows,
            }

        if report_code == "billing_snapshot":
            summary = await self._billing_metrics(tenant_id, date_from, date_to)
            rows = await self._billing_rows(tenant_id, date_from, date_to, status)
            columns = [
                {"key": "invoice_number", "label": "Invoice"},
                {"key": "status", "label": "Status"},
                {"key": "amount_cents", "label": "Amount (cents)"},
                {"key": "issued_at", "label": "Issued"},
                {"key": "due_at", "label": "Due"},
            ]
            return {
                "code": definition.code,
                "title": definition.title,
                "description": definition.description,
                "filters": filters,
                "summary": summary,
                "columns": columns,
                "rows": rows,
            }

        raise ValueError("Unknown report")

    async def export_report(
        self,
        tenant_id: UUID,
        report_code: str,
        export_format: str,
        date_from: datetime | None,
        date_to: datetime | None,
        requested_by: UUID | None,
        status_filter: str | None = None,
    ) -> ReportExport:
        export_format = export_format.lower()
        if export_format not in {"csv", "pdf", "excel"}:
            raise ValueError("Unsupported export format")
        if report_code not in REPORT_DEFINITIONS:
            raise ValueError("Unknown report")

        export = ReportExport(
            report_code=report_code,
            scope="hotel",
            export_format=export_format,
            status="pending",
            requested_by=requested_by,
            tenant_id=tenant_id,
            filters={
                "date_from": date_from.isoformat() if date_from else None,
                "date_to": date_to.isoformat() if date_to else None,
                "status": status_filter,
            },
        )
        self.session.add(export)
        await self.session.commit()
        await self.session.refresh(export)
        return export

    async def get_export(self, tenant_id: UUID, export_id: UUID) -> ReportExport | None:
        stmt = select(ReportExport).where(
            ReportExport.id == export_id, ReportExport.tenant_id == tenant_id
        )
        return await self.session.scalar(stmt)

    async def _guest_metrics(
        self, tenant_id: UUID, date_from: datetime | None, date_to: datetime | None
    ) -> list[dict[str, Any]]:
        total_stmt = select(func.count()).select_from(Guest).where(Guest.tenant_id == tenant_id)
        total_stmt = apply_date_filter(total_stmt, Guest.created_at, date_from, date_to)
        total = await self.session.scalar(total_stmt)

        active_stmt = select(func.count()).select_from(Guest).where(
            Guest.tenant_id == tenant_id, Guest.status == "active"
        )
        active_stmt = apply_date_filter(active_stmt, Guest.created_at, date_from, date_to)
        active = await self.session.scalar(active_stmt)

        checked_out_stmt = select(func.count()).select_from(Guest).where(
            Guest.tenant_id == tenant_id, Guest.status == "checked_out"
        )
        checked_out_stmt = apply_date_filter(checked_out_stmt, Guest.created_at, date_from, date_to)
        checked_out = await self.session.scalar(checked_out_stmt)

        now = datetime.now(timezone.utc)
        upcoming_stmt = select(func.count()).select_from(Guest).where(
            Guest.tenant_id == tenant_id,
            Guest.check_in_at.is_not(None),
            Guest.check_in_at >= now,
        )
        if date_from or date_to:
            upcoming_stmt = apply_date_filter(upcoming_stmt, Guest.check_in_at, date_from, date_to)
        upcoming = await self.session.scalar(upcoming_stmt)

        return [
            {"label": "Guests", "value": int(total or 0)},
            {"label": "Active", "value": int(active or 0)},
            {"label": "Checked Out", "value": int(checked_out or 0)},
            {"label": "Upcoming Check-ins", "value": int(upcoming or 0)},
        ]

    async def _room_metrics(
        self, tenant_id: UUID, date_from: datetime | None, date_to: datetime | None
    ) -> list[dict[str, Any]]:
        total_stmt = select(func.count()).select_from(Room).where(Room.tenant_id == tenant_id)
        total_stmt = apply_date_filter(total_stmt, Room.created_at, date_from, date_to)
        total = await self.session.scalar(total_stmt)

        available_stmt = select(func.count()).select_from(Room).where(
            Room.tenant_id == tenant_id, Room.status == "available"
        )
        available_stmt = apply_date_filter(available_stmt, Room.created_at, date_from, date_to)
        available = await self.session.scalar(available_stmt)

        occupied_stmt = select(func.count()).select_from(Room).where(
            Room.tenant_id == tenant_id, Room.status == "occupied"
        )
        occupied_stmt = apply_date_filter(occupied_stmt, Room.created_at, date_from, date_to)
        occupied = await self.session.scalar(occupied_stmt)

        maintenance_stmt = select(func.count()).select_from(Room).where(
            Room.tenant_id == tenant_id, Room.status == "maintenance"
        )
        maintenance_stmt = apply_date_filter(maintenance_stmt, Room.created_at, date_from, date_to)
        maintenance = await self.session.scalar(maintenance_stmt)

        return [
            {"label": "Rooms", "value": int(total or 0)},
            {"label": "Available", "value": int(available or 0)},
            {"label": "Occupied", "value": int(occupied or 0)},
            {"label": "Maintenance", "value": int(maintenance or 0)},
        ]

    async def _incident_metrics(
        self, tenant_id: UUID, date_from: datetime | None, date_to: datetime | None
    ) -> list[dict[str, Any]]:
        date_column = func.coalesce(Incident.occurred_at, Incident.created_at)
        total_stmt = select(func.count()).select_from(Incident).where(Incident.tenant_id == tenant_id)
        total_stmt = apply_date_filter(total_stmt, date_column, date_from, date_to)
        total = await self.session.scalar(total_stmt)

        open_stmt = select(func.count()).select_from(Incident).where(
            Incident.tenant_id == tenant_id, Incident.status == "open"
        )
        open_stmt = apply_date_filter(open_stmt, date_column, date_from, date_to)
        open_count = await self.session.scalar(open_stmt)

        resolved_stmt = select(func.count()).select_from(Incident).where(
            Incident.tenant_id == tenant_id, Incident.status == "resolved"
        )
        resolved_stmt = apply_date_filter(resolved_stmt, date_column, date_from, date_to)
        resolved_count = await self.session.scalar(resolved_stmt)

        high_stmt = select(func.count()).select_from(Incident).where(
            Incident.tenant_id == tenant_id, Incident.severity == "high"
        )
        high_stmt = apply_date_filter(high_stmt, date_column, date_from, date_to)
        high_count = await self.session.scalar(high_stmt)

        return [
            {"label": "Incidents", "value": int(total or 0)},
            {"label": "Open", "value": int(open_count or 0)},
            {"label": "Resolved", "value": int(resolved_count or 0)},
            {"label": "High Severity", "value": int(high_count or 0)},
        ]

    async def _kiosk_metrics(
        self, tenant_id: UUID, date_from: datetime | None, date_to: datetime | None
    ) -> list[dict[str, Any]]:
        total_stmt = select(func.count()).select_from(Kiosk).where(Kiosk.tenant_id == tenant_id)
        total_stmt = apply_date_filter(total_stmt, Kiosk.created_at, date_from, date_to)
        total = await self.session.scalar(total_stmt)

        active_stmt = select(func.count()).select_from(Kiosk).where(
            Kiosk.tenant_id == tenant_id, Kiosk.status == "active"
        )
        active_stmt = apply_date_filter(active_stmt, Kiosk.created_at, date_from, date_to)
        active_count = await self.session.scalar(active_stmt)

        inactive_stmt = select(func.count()).select_from(Kiosk).where(
            Kiosk.tenant_id == tenant_id, Kiosk.status != "active"
        )
        inactive_stmt = apply_date_filter(inactive_stmt, Kiosk.created_at, date_from, date_to)
        inactive_count = await self.session.scalar(inactive_stmt)

        now = datetime.now(timezone.utc)
        recent_stmt = select(func.count()).select_from(Kiosk).where(
            Kiosk.tenant_id == tenant_id,
            Kiosk.last_seen_at.is_not(None),
            Kiosk.last_seen_at >= now - timedelta(hours=24),
        )
        if date_from or date_to:
            recent_stmt = apply_date_filter(recent_stmt, Kiosk.last_seen_at, date_from, date_to)
        recent_count = await self.session.scalar(recent_stmt)

        return [
            {"label": "Kiosks", "value": int(total or 0)},
            {"label": "Active", "value": int(active_count or 0)},
            {"label": "Inactive", "value": int(inactive_count or 0)},
            {"label": "Seen < 24h", "value": int(recent_count or 0)},
        ]

    async def _billing_metrics(
        self, tenant_id: UUID, date_from: datetime | None, date_to: datetime | None
    ) -> list[dict[str, Any]]:
        total_stmt = select(func.count()).select_from(Invoice).where(Invoice.tenant_id == tenant_id)
        total_stmt = apply_date_filter(total_stmt, Invoice.issued_at, date_from, date_to)
        total = await self.session.scalar(total_stmt)

        outstanding_stmt = select(func.count()).select_from(Invoice).where(
            Invoice.tenant_id == tenant_id, Invoice.status != "paid"
        )
        outstanding_stmt = apply_date_filter(outstanding_stmt, Invoice.issued_at, date_from, date_to)
        outstanding = await self.session.scalar(outstanding_stmt)

        balance_stmt = select(func.coalesce(func.sum(Invoice.amount_cents), 0)).select_from(Invoice).where(
            Invoice.tenant_id == tenant_id, Invoice.status != "paid"
        )
        balance_stmt = apply_date_filter(balance_stmt, Invoice.issued_at, date_from, date_to)
        balance = await self.session.scalar(balance_stmt)

        return [
            {"label": "Invoices", "value": int(total or 0)},
            {"label": "Outstanding", "value": int(outstanding or 0)},
            {"label": "Balance (cents)", "value": int(balance or 0)},
        ]

    async def _guest_rows(
        self,
        tenant_id: UUID,
        date_from: datetime | None,
        date_to: datetime | None,
        status: str | None,
    ) -> list[dict[str, Any]]:
        stmt = select(Guest).where(Guest.tenant_id == tenant_id)
        if status:
            stmt = stmt.where(Guest.status == status)
        stmt = apply_date_filter(stmt, Guest.created_at, date_from, date_to)
        stmt = stmt.order_by(Guest.check_in_at.desc().nullslast(), Guest.created_at.desc())
        result = await self.session.execute(stmt)
        rows = []
        for guest in result.scalars().all():
            rows.append(
                {
                    "guest": f"{guest.first_name} {guest.last_name}",
                    "status": guest.status,
                    "check_in_at": guest.check_in_at,
                    "check_out_at": guest.check_out_at,
                    "email": guest.email,
                }
            )
        return rows

    async def _room_rows(
        self,
        tenant_id: UUID,
        date_from: datetime | None,
        date_to: datetime | None,
        status: str | None,
    ) -> list[dict[str, Any]]:
        stmt = select(Room).where(Room.tenant_id == tenant_id)
        if status:
            stmt = stmt.where(Room.status == status)
        stmt = apply_date_filter(stmt, Room.created_at, date_from, date_to)
        stmt = stmt.order_by(Room.number.asc())
        result = await self.session.execute(stmt)
        rows = []
        for room in result.scalars().all():
            rows.append(
                {
                    "room_number": room.number,
                    "room_type": room.room_type,
                    "status": room.status,
                    "floor": room.floor,
                    "rate_cents": room.rate_cents,
                }
            )
        return rows

    async def _incident_rows(
        self,
        tenant_id: UUID,
        date_from: datetime | None,
        date_to: datetime | None,
        status: str | None,
    ) -> list[dict[str, Any]]:
        stmt = select(Incident).where(Incident.tenant_id == tenant_id)
        if status:
            stmt = stmt.where(Incident.status == status)
        date_column = func.coalesce(Incident.occurred_at, Incident.created_at)
        stmt = apply_date_filter(stmt, date_column, date_from, date_to)
        stmt = stmt.order_by(Incident.occurred_at.desc().nullslast(), Incident.created_at.desc())
        result = await self.session.execute(stmt)
        rows = []
        for incident in result.scalars().all():
            rows.append(
                {
                    "title": incident.title,
                    "status": incident.status,
                    "severity": incident.severity,
                    "occurred_at": incident.occurred_at,
                    "resolved_at": incident.resolved_at,
                }
            )
        return rows

    async def _kiosk_rows(
        self,
        tenant_id: UUID,
        date_from: datetime | None,
        date_to: datetime | None,
        status: str | None,
    ) -> list[dict[str, Any]]:
        stmt = select(Kiosk).where(Kiosk.tenant_id == tenant_id)
        if status:
            stmt = stmt.where(Kiosk.status == status)
        stmt = apply_date_filter(stmt, Kiosk.created_at, date_from, date_to)
        stmt = stmt.order_by(Kiosk.name.asc())
        result = await self.session.execute(stmt)
        rows = []
        for kiosk in result.scalars().all():
            rows.append(
                {
                    "name": kiosk.name,
                    "location": kiosk.location,
                    "status": kiosk.status,
                    "last_seen_at": kiosk.last_seen_at,
                }
            )
        return rows

    async def _billing_rows(
        self,
        tenant_id: UUID,
        date_from: datetime | None,
        date_to: datetime | None,
        status: str | None,
    ) -> list[dict[str, Any]]:
        stmt = select(Invoice).where(Invoice.tenant_id == tenant_id)
        if status:
            stmt = stmt.where(Invoice.status == status)
        stmt = apply_date_filter(stmt, Invoice.issued_at, date_from, date_to)
        stmt = stmt.order_by(Invoice.issued_at.desc())
        result = await self.session.execute(stmt)
        rows = []
        for invoice in result.scalars().all():
            rows.append(
                {
                    "invoice_number": invoice.invoice_number,
                    "status": invoice.status,
                    "amount_cents": invoice.amount_cents,
                    "issued_at": invoice.issued_at,
                    "due_at": invoice.due_at,
                }
            )
        return rows

