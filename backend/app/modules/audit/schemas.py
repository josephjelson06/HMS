from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel


class AuditLogItem(BaseModel):
    """Response schema for a single audit log entry."""
    id: UUID
    tenant_id: UUID | None = None
    actor_user_id: UUID | None = None
    acting_as_user_id: UUID | None = None
    action: str
    metadata: dict[str, Any] = {}
    resource_type: str | None = None
    resource_id: str | None = None
    ip_address: str | None = None
    user_agent: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class AuditLogListResponse(BaseModel):
    """Response schema for paginated audit log list."""
    items: list[AuditLogItem]
    total: int
    limit: int
    offset: int
