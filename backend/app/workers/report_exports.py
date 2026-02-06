import asyncio
import logging
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.core.storage import ReportStorage
from app.models.report_export import ReportExport
from app.modules.admin.reports.service import ReportService
from app.modules.hotel.reports.service import HotelReportService

logger = logging.getLogger(__name__)

_worker_task: asyncio.Task | None = None


def start_report_export_worker() -> None:
    global _worker_task
    if _worker_task and not _worker_task.done():
        return
    _worker_task = asyncio.create_task(_worker_loop())


async def stop_report_export_worker() -> None:
    global _worker_task
    if _worker_task:
        _worker_task.cancel()
        try:
            await _worker_task
        except asyncio.CancelledError:
            pass
        _worker_task = None


async def _worker_loop() -> None:
    while True:
        try:
            await _process_pending_exports()
        except Exception:  # pragma: no cover
            logger.exception("Report export worker iteration failed")
        await asyncio.sleep(max(settings.report_export_poll_seconds, 1))


async def _process_pending_exports() -> None:
    async with AsyncSessionLocal() as session:
        stmt = (
            select(ReportExport)
            .where(ReportExport.status == "pending")
            .order_by(ReportExport.created_at.asc())
            .limit(max(settings.report_export_batch_size, 1))
        )
        result = await session.execute(stmt)
        pending = result.scalars().all()

    for item in pending:
        await _process_one_export(item.id)


async def _process_one_export(export_id) -> None:
    storage = ReportStorage(settings.reports_storage_path)

    async with AsyncSessionLocal() as session:
        export = await session.get(ReportExport, export_id)
        if not export or export.status != "pending":
            return

        export.status = "processing"
        export.error_message = None
        session.add(export)
        await session.commit()

    async with AsyncSessionLocal() as session:
        export = await session.get(ReportExport, export_id)
        if not export:
            return

        try:
            filters = export.filters or {}
            date_from = _parse_datetime(filters.get("date_from"))
            date_to = _parse_datetime(filters.get("date_to"))
            status_filter = _clean_status(filters.get("status"))

            if export.scope == "hotel":
                if export.tenant_id is None:
                    raise ValueError("Hotel export requires tenant context")
                report_service = HotelReportService(session)
                report = await report_service.get_report(
                    tenant_id=export.tenant_id,
                    report_code=export.report_code,
                    date_from=date_from,
                    date_to=date_to,
                    status=status_filter,
                )
            elif export.scope == "admin":
                report_service = ReportService(session)
                report = await report_service.get_report(
                    report_code=export.report_code,
                    date_from=date_from,
                    date_to=date_to,
                    status=status_filter,
                )
            else:
                raise ValueError("Unsupported report scope")

            file_path, file_name = storage.save_export(
                report_code=export.report_code,
                export_format=export.export_format,
                columns=report.get("columns", []),
                rows=report.get("rows", []),
                title=report.get("title"),
            )

            export.status = "completed"
            export.file_path = file_path
            export.file_name = file_name
            export.completed_at = datetime.now(timezone.utc)
            export.error_message = None
        except Exception as exc:  # pragma: no cover
            export.status = "failed"
            export.error_message = str(exc)
            export.completed_at = datetime.now(timezone.utc)
            logger.exception("Report export %s failed", export_id)

        session.add(export)
        await session.commit()


def _parse_datetime(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        raw = value.strip()
        if not raw:
            return None
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    return None


def _clean_status(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None
