from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.audit.context import get_audit_runtime_context


async def audit_event_stub(
    *,
    action: str,
    session: AsyncSession | None = None,
    metadata: dict[str, Any] | None = None,
    resource_type: str | None = None,
    resource_id: str | None = None,
    tenant_id: UUID | None = None,
    actor_user_id: UUID | None = None,
    acting_as_user_id: UUID | None = None,
) -> None:
    """Emit an audit log entry using the current request's context.
    
    This is the primary audit API. Call it from anywhere in the request lifecycle:
    
        await audit_event_stub(
            action="user.created",
            metadata={"email": user.email},
            resource_type="user",
            resource_id=str(user.id),
        )
    
    Fields auto-populated from AuditRuntimeContext (if not explicitly provided):
    - tenant_id
    - actor_user_id
    - acting_as_user_id
    - ip_address
    - user_agent
    
    HMS-specific fields (resource_type, resource_id) are passed explicitly.
    """
    ctx = get_audit_runtime_context()
    effective_session = session or (ctx.session if ctx else None)
    
    if effective_session is None:
        # Not in a request context — silently skip.
        # This allows audit calls in tests or CLI without crashing.
        return

    from app.modules.audit.service import append_audit_log

    await append_audit_log(
        session=effective_session,
        action=action,
        tenant_id=tenant_id or (ctx.tenant_id if ctx else None),
        actor_user_id=actor_user_id or (ctx.actor_user_id if ctx else None),
        acting_as_user_id=acting_as_user_id or (ctx.acting_as_user_id if ctx else None),
        metadata=metadata if metadata is not None else {},
        resource_type=resource_type,
        resource_id=resource_id,
        ip_address=ctx.ip_address if ctx else None,
        user_agent=ctx.user_agent if ctx else None,
    )
