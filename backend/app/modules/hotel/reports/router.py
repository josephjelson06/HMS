from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.modules.auth.dependencies import CurrentUser, get_current_user, require_permission
from app.modules.hotel.reports.schemas import (
    ReportCard,
    ReportDetail,
    ReportExportOut,
    ReportExportRequest,
    ReportsListResponse,
)
from app.modules.hotel.reports.service import HotelReportService


router = APIRouter()


@router.get(
    "/exports/{export_id}",
    response_model=ReportExportOut,
    dependencies=[Depends(require_permission("hotel:reports:export"))],
)
async def get_export(
    export_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ReportExportOut:
    if current_user.tenant_id is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Tenant context missing")

    service = HotelReportService(session)
    try:
        export_uuid = UUID(export_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid export id") from exc

    export = await service.get_export(current_user.tenant_id, export_uuid)
    if not export:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Export not found")

    download_path = None
    if export.status == "completed" and export.file_path:
        download_path = f"/hotel/reports/exports/{export.id}/download"

    return ReportExportOut.model_validate(export).model_copy(update={"download_path": download_path})


@router.get(
    "/exports/{export_id}/download",
    dependencies=[Depends(require_permission("hotel:reports:export"))],
)
async def download_export(
    export_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> FileResponse:
    if current_user.tenant_id is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Tenant context missing")

    service = HotelReportService(session)
    try:
        export_uuid = UUID(export_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid export id") from exc

    export = await service.get_export(current_user.tenant_id, export_uuid)
    if not export:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Export not found")
    if export.status in {"pending", "processing"}:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Export is still processing")
    if export.status == "failed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=export.error_message or "Export failed",
        )
    if not export.file_path:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Export file not found")

    extension = export.export_format.lower()
    return FileResponse(export.file_path, filename=export.file_name or f"report.{extension}")


@router.get(
    "/",
    response_model=ReportsListResponse,
    dependencies=[Depends(require_permission("hotel:reports:read"))],
)
async def list_reports(
    date_from: datetime | None = Query(None),
    date_to: datetime | None = Query(None),
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ReportsListResponse:
    if current_user.tenant_id is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Tenant context missing")

    service = HotelReportService(session)
    items = await service.list_reports(current_user.tenant_id, date_from, date_to)
    return ReportsListResponse(items=[ReportCard.model_validate(item) for item in items])


@router.get(
    "/{report_code}",
    response_model=ReportDetail,
    dependencies=[Depends(require_permission("hotel:reports:read"))],
)
async def get_report(
    report_code: str,
    date_from: datetime | None = Query(None),
    date_to: datetime | None = Query(None),
    status_filter: str | None = Query(None, alias="status"),
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ReportDetail:
    if current_user.tenant_id is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Tenant context missing")

    service = HotelReportService(session)
    try:
        report = await service.get_report(
            tenant_id=current_user.tenant_id,
            report_code=report_code,
            date_from=date_from,
            date_to=date_to,
            status=status_filter,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return ReportDetail.model_validate(report)


@router.post(
    "/{report_code}/export",
    response_model=ReportExportOut,
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[Depends(require_permission("hotel:reports:export"))],
)
async def export_report(
    report_code: str,
    payload: ReportExportRequest,
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ReportExportOut:
    if current_user.tenant_id is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Tenant context missing")

    service = HotelReportService(session)
    try:
        export = await service.export_report(
            tenant_id=current_user.tenant_id,
            report_code=report_code,
            export_format=payload.export_format,
            date_from=payload.date_from,
            date_to=payload.date_to,
            requested_by=current_user.id,
            status_filter=payload.status,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return ReportExportOut.model_validate(export)
