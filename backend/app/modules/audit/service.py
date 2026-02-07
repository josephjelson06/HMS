from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import AuditLog


async def append_audit_log(
    session: AsyncSession,
    *,
    action: str,
    tenant_id: UUID | None = None,
    actor_user_id: UUID | None = None,
    acting_as_user_id: UUID | None = None,
    metadata: dict[str, Any] | None = None,
    resource_type: str | None = None,
    resource_id: str | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> AuditLog:
    """Insert a single audit log row.
    
    This function uses HMS's existing AuditLog model. It maps the AuthModule-style
    field names (actor_user_id, acting_as_user_id, metadata) to the current HMS model
    field names (user_id, impersonated_by, changes) until PR 5's migration is applied.
    """
    # Build kwargs, mapping new names to old column names in the model
    kwargs: dict[str, Any] = {
        "action": action,
        "changes": metadata or {},  # Map metadata -> changes
    }
    
    if tenant_id is not None:
        kwargs["tenant_id"] = tenant_id
    if actor_user_id is not None:
        kwargs["user_id"] = actor_user_id  # Map actor_user_id -> user_id
    if acting_as_user_id is not None:
        kwargs["impersonated_by"] = acting_as_user_id  # Map acting_as_user_id -> impersonated_by
    if ip_address is not None:
        kwargs["ip_address"] = ip_address
    if user_agent is not None:
        kwargs["user_agent"] = user_agent
    if resource_type is not None:
        kwargs["resource_type"] = resource_type
    if resource_id is not None:
        kwargs["resource_id"] = resource_id

    entry = AuditLog(**kwargs)
    session.add(entry)
    await session.flush()
    return entry


async def list_audit_logs(
    session: AsyncSession,
    *,
    tenant_id: UUID | None = None,
    actor_user_id: UUID | None = None,
    action: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[AuditLog]:
    """Query audit logs with optional filters.
    
    This can be used by the existing admin/audit and hotel/audit routers.
    Maps actor_user_id to the current model's user_id field.
    """
    stmt = select(AuditLog).order_by(desc(AuditLog.created_at))

    if tenant_id is not None:
        stmt = stmt.where(AuditLog.tenant_id == tenant_id)
    if actor_user_id is not None:
        stmt = stmt.where(AuditLog.user_id == actor_user_id)  # Map to user_id
    if action is not None:
        stmt = stmt.where(AuditLog.action == action)

    stmt = stmt.limit(limit).offset(offset)
    result = await session.execute(stmt)
    return list(result.scalars().all())
