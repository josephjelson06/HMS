from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class AuditLogItem(BaseModel):
    """Response schema for a single audit log entry.
    
    Maps HMS model fields (user_id, changes, impersonated_by) to 
    AuthModule-style names (actor_user_id, metadata, acting_as_user_id).
    """
    id: UUID
    tenant_id: UUID | None = None
    actor_user_id: UUID | None = Field(None, alias="user_id")
    acting_as_user_id: UUID | None = Field(None, alias="impersonated_by")
    action: str
    metadata: dict[str, Any] = Field(default_factory=dict, alias="changes")
    resource_type: str | None = None
    resource_id: str | None = None
    ip_address: str | None = None
    user_agent: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class AuditLogListResponse(BaseModel):
    """Response schema for paginated audit log list."""
    items: list[AuditLogItem]
    total: int
    limit: int
    offset: int
