from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.core.config import settings
from app.core.storage import ReportStorage
from app.models.invoice import Invoice
from app.models.plan import Plan
from app.models.report_export import ReportExport
from app.models.subscription import Subscription
from app.models.tenant import Tenant
from app.models.user import User


@dataclass(frozen=True)
class ReportDefinition:
    code: str
    title: str
    description: str


REPORT_DEFINITIONS = {
    "platform_overview": ReportDefinition(
        code="platform_overview",
        title="Platform Overview",
        description="Core KPIs across tenants, subscriptions, and revenue.",
    ),
    "tenant_growth": ReportDefinition(
        code="tenant_growth",
        title="Tenant Growth",
        description="Monthly tenant onboarding trends.",
    ),
    "subscription_health": ReportDefinition(
        code="subscription_health",
        title="Subscription Health",
        description="Current subscription statuses and renewal windows.",
    ),
    "revenue_snapshot": ReportDefinition(
        code="revenue_snapshot",
        title="Revenue Snapshot",
        description="Monthly billed vs paid totals from invoices.",
    ),
    "invoice_aging": ReportDefinition(
        code="invoice_aging",
        title="Invoice Aging",
        description="Outstanding invoices and overdue exposure.",
    ),
}


def apply_date_filter(stmt, column, date_from: datetime | None, date_to: datetime | None):
    if date_from:
        stmt = stmt.where(column >= date_from)
    if date_to:
        stmt = stmt.where(column <= date_to)
    return stmt


class ReportService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.storage = ReportStorage(settings.reports_storage_path)

    async def list_reports(
        self, date_from: datetime | None = None, date_to: datetime | None = None
    ) -> list[dict[str, Any]]:
        metrics = await self._overview_metrics(date_from, date_to)
        subscription_metrics = await self._subscription_metrics()
        invoice_metrics = await self._invoice_metrics(date_from, date_to)
        tenant_metrics = await self._tenant_metrics(date_from, date_to)
        revenue_metrics = await self._revenue_metrics(date_from, date_to)

        return [
            {
                "code": REPORT_DEFINITIONS["platform_overview"].code,
                "title": REPORT_DEFINITIONS["platform_overview"].title,
                "description": REPORT_DEFINITIONS["platform_overview"].description,
                "metrics": metrics,
            },
            {
                "code": REPORT_DEFINITIONS["tenant_growth"].code,
                "title": REPORT_DEFINITIONS["tenant_growth"].title,
                "description": REPORT_DEFINITIONS["tenant_growth"].description,
                "metrics": tenant_metrics,
            },
            {
                "code": REPORT_DEFINITIONS["subscription_health"].code,
                "title": REPORT_DEFINITIONS["subscription_health"].title,
                "description": REPORT_DEFINITIONS["subscription_health"].description,
                "metrics": subscription_metrics,
            },
            {
                "code": REPORT_DEFINITIONS["revenue_snapshot"].code,
                "title": REPORT_DEFINITIONS["revenue_snapshot"].title,
                "description": REPORT_DEFINITIONS["revenue_snapshot"].description,
                "metrics": revenue_metrics,
            },
            {
                "code": REPORT_DEFINITIONS["invoice_aging"].code,
                "title": REPORT_DEFINITIONS["invoice_aging"].title,
                "description": REPORT_DEFINITIONS["invoice_aging"].description,
                "metrics": invoice_metrics,
            },
        ]

    async def get_report(
        self,
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

        if report_code == "platform_overview":
            summary = await self._overview_metrics(date_from, date_to)
            return {
                "code": definition.code,
                "title": definition.title,
                "description": definition.description,
                "filters": filters,
                "summary": summary,
                "columns": [],
                "rows": [],
            }

        if report_code == "tenant_growth":
            summary = await self._tenant_metrics(date_from, date_to)
            rows = await self._tenant_growth_rows(date_from, date_to)
            columns = [
                {"key": "month", "label": "Month"},
                {"key": "new_hotels", "label": "New Hotels"},
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

        if report_code == "subscription_health":
            summary = await self._subscription_metrics()
            rows = await self._subscription_rows(date_from, date_to, status)
            columns = [
                {"key": "hotel_name", "label": "Hotel"},
                {"key": "plan_name", "label": "Plan"},
                {"key": "status", "label": "Status"},
                {"key": "period_end", "label": "Period End"},
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

        if report_code == "revenue_snapshot":
            summary = await self._revenue_metrics(date_from, date_to)
            rows = await self._revenue_rows(date_from, date_to)
            columns = [
                {"key": "month", "label": "Month"},
                {"key": "total_billed", "label": "Total Billed (cents)"},
                {"key": "total_paid", "label": "Total Paid (cents)"},
                {"key": "total_outstanding", "label": "Outstanding (cents)"},
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

        if report_code == "invoice_aging":
            summary = await self._invoice_metrics(date_from, date_to)
            rows = await self._invoice_rows(date_from, date_to)
            columns = [
                {"key": "invoice_number", "label": "Invoice"},
                {"key": "hotel_name", "label": "Hotel"},
                {"key": "amount_cents", "label": "Amount (cents)"},
                {"key": "status", "label": "Status"},
                {"key": "due_at", "label": "Due Date"},
                {"key": "days_overdue", "label": "Days Overdue"},
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
        report_code: str,
        export_format: str,
        date_from: datetime | None,
        date_to: datetime | None,
        requested_by: UUID | None,
        tenant_id: UUID | None,
        status_filter: str | None = None,
    ) -> ReportExport:
        export_format = export_format.lower()
        if export_format not in {"csv", "pdf", "excel"}:
            raise ValueError("Unsupported export format")
        if report_code not in REPORT_DEFINITIONS:
            raise ValueError("Unknown report")

        export = ReportExport(
            report_code=report_code,
            scope="admin",
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

    async def get_export(self, export_id: UUID) -> ReportExport | None:
        return await self.session.get(ReportExport, export_id)

    async def _overview_metrics(self, date_from: datetime | None, date_to: datetime | None) -> list[dict[str, Any]]:
        total_hotels = await self.session.scalar(select(func.count()).select_from(Tenant))
        total_admins = await self.session.scalar(
            select(func.count()).select_from(User).where(User.user_type == "platform")
        )
        total_hotel_users = await self.session.scalar(
            select(func.count()).select_from(User).where(User.user_type == "hotel")
        )
        active_subscriptions = await self.session.scalar(
            select(func.count()).select_from(Subscription).where(Subscription.status == "active")
        )

        revenue_stmt = select(func.coalesce(func.sum(Invoice.amount_cents), 0)).select_from(Invoice)
        revenue_stmt = apply_date_filter(revenue_stmt, Invoice.issued_at, date_from, date_to)
        revenue_total = await self.session.scalar(revenue_stmt)

        return [
            {"label": "Hotels", "value": int(total_hotels or 0)},
            {"label": "Admin Users", "value": int(total_admins or 0)},
            {"label": "Hotel Users", "value": int(total_hotel_users or 0)},
            {"label": "Active Subscriptions", "value": int(active_subscriptions or 0)},
            {"label": "Revenue (cents)", "value": int(revenue_total or 0)},
        ]

    async def _tenant_metrics(self, date_from: datetime | None, date_to: datetime | None) -> list[dict[str, Any]]:
        stmt = select(func.count()).select_from(Tenant)
        stmt = apply_date_filter(stmt, Tenant.created_at, date_from, date_to)
        new_hotels = await self.session.scalar(stmt)
        return [{"label": "New Hotels", "value": int(new_hotels or 0)}]

    async def _subscription_metrics(self) -> list[dict[str, Any]]:
        total = await self.session.scalar(select(func.count()).select_from(Subscription))
        active = await self.session.scalar(
            select(func.count()).select_from(Subscription).where(Subscription.status == "active")
        )
        canceled = await self.session.scalar(
            select(func.count()).select_from(Subscription).where(Subscription.status == "canceled")
        )
        return [
            {"label": "Total Subscriptions", "value": int(total or 0)},
            {"label": "Active", "value": int(active or 0)},
            {"label": "Canceled", "value": int(canceled or 0)},
        ]

    async def _invoice_metrics(self, date_from: datetime | None, date_to: datetime | None) -> list[dict[str, Any]]:
        stmt = select(func.count()).select_from(Invoice)
        stmt = apply_date_filter(stmt, Invoice.issued_at, date_from, date_to)
        total = await self.session.scalar(stmt)

        overdue_stmt = select(func.count()).select_from(Invoice).where(
            Invoice.due_at.is_not(None),
            Invoice.status != "paid",
            Invoice.due_at < datetime.now(timezone.utc),
        )
        overdue = await self.session.scalar(overdue_stmt)
        return [
            {"label": "Invoices", "value": int(total or 0)},
            {"label": "Overdue", "value": int(overdue or 0)},
        ]

    async def _revenue_metrics(self, date_from: datetime | None, date_to: datetime | None) -> list[dict[str, Any]]:
        billed_stmt = select(func.coalesce(func.sum(Invoice.amount_cents), 0)).select_from(Invoice)
        billed_stmt = apply_date_filter(billed_stmt, Invoice.issued_at, date_from, date_to)
        total_billed = await self.session.scalar(billed_stmt)

        paid_stmt = (
            select(func.coalesce(func.sum(Invoice.amount_cents), 0))
            .select_from(Invoice)
            .where(Invoice.status == "paid")
        )
        paid_stmt = apply_date_filter(paid_stmt, Invoice.issued_at, date_from, date_to)
        total_paid = await self.session.scalar(paid_stmt)

        outstanding = int(total_billed or 0) - int(total_paid or 0)
        return [
            {"label": "Billed (cents)", "value": int(total_billed or 0)},
            {"label": "Paid (cents)", "value": int(total_paid or 0)},
            {"label": "Outstanding (cents)", "value": outstanding},
        ]

    async def _tenant_growth_rows(
        self, date_from: datetime | None, date_to: datetime | None
    ) -> list[dict[str, Any]]:
        stmt = select(
            func.date_trunc("month", Tenant.created_at).label("month"),
            func.count().label("count"),
        )
        stmt = apply_date_filter(stmt, Tenant.created_at, date_from, date_to)
        stmt = stmt.group_by("month").order_by("month")
        result = await self.session.execute(stmt)
        rows = []
        for month, count in result.all():
            month_label = month.strftime("%Y-%m") if month else "unknown"
            rows.append({"month": month_label, "new_hotels": int(count or 0)})
        return rows

    async def _subscription_rows(
        self, date_from: datetime | None, date_to: datetime | None, status: str | None
    ) -> list[dict[str, Any]]:
        stmt = (
            select(Subscription, Tenant.name, Plan.name)
            .join(Tenant, Tenant.id == Subscription.tenant_id)
            .join(Plan, Plan.id == Subscription.plan_id)
            .order_by(Subscription.current_period_end.desc())
        )
        if status:
            stmt = stmt.where(Subscription.status == status)
        if date_from or date_to:
            stmt = apply_date_filter(stmt, Subscription.current_period_end, date_from, date_to)
        result = await self.session.execute(stmt)
        rows = []
        for subscription, tenant_name, plan_name in result.all():
            rows.append(
                {
                    "hotel_name": tenant_name,
                    "plan_name": plan_name,
                    "status": subscription.status,
                    "period_end": subscription.current_period_end,
                }
            )
        return rows

    async def _revenue_rows(
        self, date_from: datetime | None, date_to: datetime | None
    ) -> list[dict[str, Any]]:
        stmt = select(
            func.date_trunc("month", Invoice.issued_at).label("month"),
            func.coalesce(func.sum(Invoice.amount_cents), 0).label("total_billed"),
            func.coalesce(
                func.sum(case((Invoice.status == "paid", Invoice.amount_cents), else_=0)), 0
            ).label("total_paid"),
        )
        stmt = apply_date_filter(stmt, Invoice.issued_at, date_from, date_to)
        stmt = stmt.group_by("month").order_by("month")
        result = await self.session.execute(stmt)
        rows = []
        for month, total_billed, total_paid in result.all():
            month_label = month.strftime("%Y-%m") if month else "unknown"
            billed = int(total_billed or 0)
            paid = int(total_paid or 0)
            rows.append(
                {
                    "month": month_label,
                    "total_billed": billed,
                    "total_paid": paid,
                    "total_outstanding": billed - paid,
                }
            )
        return rows

    async def _invoice_rows(
        self, date_from: datetime | None, date_to: datetime | None
    ) -> list[dict[str, Any]]:
        stmt = select(Invoice, Tenant.name).join(Tenant, Tenant.id == Invoice.tenant_id)
        stmt = apply_date_filter(stmt, Invoice.issued_at, date_from, date_to)
        stmt = stmt.order_by(Invoice.due_at.desc().nullslast())
        result = await self.session.execute(stmt)
        now = datetime.now(timezone.utc)
        rows = []
        for invoice, tenant_name in result.all():
            days_overdue = None
            if invoice.due_at and invoice.status != "paid" and invoice.due_at < now:
                days_overdue = (now - invoice.due_at).days
            rows.append(
                {
                    "invoice_number": invoice.invoice_number,
                    "hotel_name": tenant_name,
                    "amount_cents": invoice.amount_cents,
                    "status": invoice.status,
                    "due_at": invoice.due_at,
                    "days_overdue": days_overdue,
                }
            )
        return rows

