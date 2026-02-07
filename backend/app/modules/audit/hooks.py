"""Audit event hooks for tracking security-sensitive operations.

This module provides utilities for logging audit events.
"""
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import AuditLog


async def audit_event_stub(
    action: str,
    *,
    session: AsyncSession,
    user_id: str | None = None,
    tenant_id: str | None = None,
    resource_type: str | None = None,
    resource_id: str | None = None,
    metadata: dict[str, Any] | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> None:
    """Log an audit event to the database.
    
    This is a stub implementation that creates basic audit log entries.
    A full implementation would include more sophisticated features like:
    - Automatic tenant/user extraction from context
    - IP address extraction from request
    - Structured metadata validation
    - Async background processing
    
    Args:
        action: The action being performed (e.g., "password.changed", "user.invited")
        session: Database session
        user_id: ID of the user performing the action
        tenant_id: ID of the tenant context
        resource_type: Type of resource being acted upon
        resource_id: ID of the resource
        metadata: Additional structured data about the event
        ip_address: IP address of the client
        user_agent: User agent string
    """
    # Create audit log entry
    audit_entry = AuditLog(
        tenant_id=tenant_id,
        user_id=user_id,
        action=action,
        resource_type=resource_type or "system",
        resource_id=resource_id,
        changes=metadata or {},
        ip_address=ip_address,
        user_agent=user_agent,
    )
    session.add(audit_entry)
    # Note: Caller is responsible for commit
