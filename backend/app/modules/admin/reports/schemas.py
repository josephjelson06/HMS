from datetime import datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field
from uuid import UUID


ExportFormat = Literal["csv", "pdf", "excel"]


class ReportMetric(BaseModel):
    label: str
    value: str | int | float


class ReportCard(BaseModel):
    code: str
    title: str
    description: str
    metrics: list[ReportMetric]


class ReportsListResponse(BaseModel):
    items: list[ReportCard]


class ReportColumn(BaseModel):
    key: str
    label: str


class ReportDetail(BaseModel):
    code: str
    title: str
    description: str
    filters: dict[str, str | None]
    summary: list[ReportMetric]
    columns: list[ReportColumn]
    rows: list[dict[str, str | int | float | datetime | None]]


class ReportExportRequest(BaseModel):
    export_format: ExportFormat = Field(alias="format")
    date_from: datetime | None = None
    date_to: datetime | None = None
    status: str | None = None


class ReportExportOut(BaseModel):
    id: UUID
    report_code: str
    export_format: str
    status: str
    file_name: str | None = None
    download_path: str | None = None
    error_message: str | None = None
    created_at: datetime | None = None
    completed_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
