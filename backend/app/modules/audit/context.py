from __future__ import annotations

from contextvars import ContextVar
from dataclasses import dataclass
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession


@dataclass
class AuditRuntimeContext:
    """Holds request-scoped state needed to emit audit log entries.
    
    Set by middleware at the start of each request.
    Read by audit_event_stub() to auto-populate fields.
    """
    session: AsyncSession | None = None
    tenant_id: UUID | None = None
    actor_user_id: UUID | None = None
    acting_as_user_id: UUID | None = None
    ip_address: str | None = None
    user_agent: str | None = None


_audit_context_var: ContextVar[AuditRuntimeContext | None] = ContextVar(
    "audit_runtime_context", default=None
)


def set_audit_runtime_context(ctx: AuditRuntimeContext) -> None:
    """Set the audit runtime context for the current request."""
    _audit_context_var.set(ctx)


def get_audit_runtime_context() -> AuditRuntimeContext | None:
    """Get the audit runtime context for the current request.
    
    Returns None if not in a request context (e.g., background task, CLI).
    """
    return _audit_context_var.get()


def clear_audit_runtime_context() -> None:
    """Clear the audit runtime context. Called at end of request."""
    _audit_context_var.set(None)
