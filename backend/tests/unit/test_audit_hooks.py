"""Unit tests for audit hooks and service functions."""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.modules.audit.context import (
    AuditRuntimeContext,
    clear_audit_runtime_context,
    set_audit_runtime_context,
)
from app.modules.audit.hooks import audit_event_stub


@pytest.mark.asyncio
async def test_audit_event_stub_with_explicit_session():
    """Test audit_event_stub with explicitly passed session."""
    mock_session = AsyncMock()
    
    # Mock the append_audit_log function in the service module
    with patch("app.modules.audit.service.append_audit_log", new_callable=AsyncMock) as mock_append:
        await audit_event_stub(
            action="user.created",
            session=mock_session,
            metadata={"email": "test@example.com"},
            resource_type="user",
            resource_id=str(uuid4()),
        )
        
        # Verify append_audit_log was called
        assert mock_append.called
        call_args = mock_append.call_args
        assert call_args.kwargs["action"] == "user.created"
        assert call_args.kwargs["session"] == mock_session
        assert call_args.kwargs["metadata"] == {"email": "test@example.com"}
        assert call_args.kwargs["resource_type"] == "user"


@pytest.mark.asyncio
async def test_audit_event_stub_with_context():
    """Test audit_event_stub using context for values."""
    tenant_id = uuid4()
    actor_id = uuid4()
    mock_session = AsyncMock()
    
    # Set up context
    ctx = AuditRuntimeContext(
        session=mock_session,
        tenant_id=tenant_id,
        actor_user_id=actor_id,
        ip_address="192.168.1.1",
        user_agent="test-agent",
    )
    set_audit_runtime_context(ctx)
    
    try:
        with patch("app.modules.audit.service.append_audit_log", new_callable=AsyncMock) as mock_append:
            await audit_event_stub(
                action="test.action",
                metadata={"key": "value"},
            )
            
            # Verify values from context were used
            assert mock_append.called
            call_args = mock_append.call_args
            assert call_args.kwargs["tenant_id"] == tenant_id
            assert call_args.kwargs["actor_user_id"] == actor_id
            assert call_args.kwargs["ip_address"] == "192.168.1.1"
            assert call_args.kwargs["user_agent"] == "test-agent"
    finally:
        clear_audit_runtime_context()


@pytest.mark.asyncio
async def test_audit_event_stub_explicit_overrides_context():
    """Test that explicit parameters override context values."""
    ctx_tenant_id = uuid4()
    explicit_tenant_id = uuid4()
    mock_session = AsyncMock()
    
    ctx = AuditRuntimeContext(
        session=mock_session,
        tenant_id=ctx_tenant_id,
        actor_user_id=uuid4(),
    )
    set_audit_runtime_context(ctx)
    
    try:
        with patch("app.modules.audit.service.append_audit_log", new_callable=AsyncMock) as mock_append:
            await audit_event_stub(
                action="test.action",
                tenant_id=explicit_tenant_id,  # Override context value
            )
            
            # Verify explicit value was used, not context value
            assert mock_append.called
            call_args = mock_append.call_args
            assert call_args.kwargs["tenant_id"] == explicit_tenant_id
    finally:
        clear_audit_runtime_context()


@pytest.mark.asyncio
async def test_audit_event_stub_no_context_no_session():
    """Test audit_event_stub silently returns when no context and no session."""
    clear_audit_runtime_context()
    
    with patch("app.modules.audit.service.append_audit_log", new_callable=AsyncMock) as mock_append:
        # Should not crash, just return silently
        await audit_event_stub(
            action="test.action",
            metadata={"key": "value"},
        )
        
        # append_audit_log should NOT have been called
        assert not mock_append.called


@pytest.mark.asyncio
async def test_audit_event_stub_context_without_session():
    """Test audit_event_stub with context but no session."""
    ctx = AuditRuntimeContext(
        session=None,  # No session
        tenant_id=uuid4(),
        actor_user_id=uuid4(),
    )
    set_audit_runtime_context(ctx)
    
    try:
        with patch("app.modules.audit.service.append_audit_log", new_callable=AsyncMock) as mock_append:
            # Should not crash, just return silently
            await audit_event_stub(
                action="test.action",
            )
            
            # append_audit_log should NOT have been called (no session available)
            assert not mock_append.called
    finally:
        clear_audit_runtime_context()


@pytest.mark.asyncio
async def test_audit_event_stub_with_impersonation():
    """Test audit_event_stub with impersonation (acting_as_user_id)."""
    actor_id = uuid4()
    acting_as_id = uuid4()
    mock_session = AsyncMock()
    
    ctx = AuditRuntimeContext(
        session=mock_session,
        actor_user_id=actor_id,
        acting_as_user_id=acting_as_id,  # Impersonation scenario
    )
    set_audit_runtime_context(ctx)
    
    try:
        with patch("app.modules.audit.service.append_audit_log", new_callable=AsyncMock) as mock_append:
            await audit_event_stub(
                action="impersonation.test",
            )
            
            assert mock_append.called
            call_args = mock_append.call_args
            assert call_args.kwargs["actor_user_id"] == actor_id
            assert call_args.kwargs["acting_as_user_id"] == acting_as_id
    finally:
        clear_audit_runtime_context()


@pytest.mark.asyncio
async def test_audit_event_stub_with_all_fields():
    """Test audit_event_stub with all possible fields."""
    tenant_id = uuid4()
    actor_id = uuid4()
    acting_as_id = uuid4()
    resource_id = str(uuid4())
    mock_session = AsyncMock()
    
    ctx = AuditRuntimeContext(
        session=mock_session,
        tenant_id=tenant_id,
        actor_user_id=actor_id,
        acting_as_user_id=acting_as_id,
        ip_address="10.0.0.1",
        user_agent="Mozilla/5.0",
    )
    set_audit_runtime_context(ctx)
    
    try:
        with patch("app.modules.audit.service.append_audit_log", new_callable=AsyncMock) as mock_append:
            await audit_event_stub(
                action="test.action",
                metadata={"key": "value"},
                resource_type="user",
                resource_id=resource_id,
            )
            
            assert mock_append.called
            call_args = mock_append.call_args
            assert call_args.kwargs["action"] == "test.action"
            assert call_args.kwargs["tenant_id"] == tenant_id
            assert call_args.kwargs["actor_user_id"] == actor_id
            assert call_args.kwargs["acting_as_user_id"] == acting_as_id
            assert call_args.kwargs["metadata"] == {"key": "value"}
            assert call_args.kwargs["resource_type"] == "user"
            assert call_args.kwargs["resource_id"] == resource_id
            assert call_args.kwargs["ip_address"] == "10.0.0.1"
            assert call_args.kwargs["user_agent"] == "Mozilla/5.0"
    finally:
        clear_audit_runtime_context()
