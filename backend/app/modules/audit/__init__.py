"""Audit module for tracking security-sensitive operations."""
from app.modules.audit.hooks import audit_event_stub

__all__ = ["audit_event_stub"]
