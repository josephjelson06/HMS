from datetime import datetime
from pydantic import BaseModel, ConfigDict
from uuid import UUID
from typing import Any


class AuditLogOut(BaseModel):
    id: UUID
    tenant_id: UUID | None = None
    user_id: UUID | None = None
    action: str
    resource_type: str | None = None
    resource_id: UUID | None = None
    changes: dict[str, Any] | None = None
    ip_address: str | None = None
    user_agent: str | None = None
    impersonated_by: UUID | None = None
    created_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class Pagination(BaseModel):
    page: int
    limit: int
    total: int


class AuditLogListResponse(BaseModel):
    items: list[AuditLogOut]
    pagination: Pagination
