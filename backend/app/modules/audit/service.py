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
    
    This function uses HMS's existing AuditLog model with both AuthModule fields
    (actor_user_id, acting_as_user_id, metadata) and HMS-specific fields
    (resource_type, resource_id, ip_address, user_agent).
    """
    # Build kwargs, only including fields that exist on the model
    kwargs: dict[str, Any] = {
        "action": action,
        "metadata": metadata or {},
    }
    
    if tenant_id is not None:
        kwargs["tenant_id"] = tenant_id
    if actor_user_id is not None:
        kwargs["actor_user_id"] = actor_user_id
    if acting_as_user_id is not None:
        kwargs["acting_as_user_id"] = acting_as_user_id
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
    """
    stmt = select(AuditLog).order_by(desc(AuditLog.created_at))

    if tenant_id is not None:
        stmt = stmt.where(AuditLog.tenant_id == tenant_id)
    if actor_user_id is not None:
        stmt = stmt.where(AuditLog.actor_user_id == actor_user_id)
    if action is not None:
        stmt = stmt.where(AuditLog.action == action)

    stmt = stmt.limit(limit).offset(offset)
    result = await session.execute(stmt)
    return list(result.scalars().all())
