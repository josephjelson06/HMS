"""Integration test demonstrating the audit logging system."""

import asyncio
from uuid import uuid4

import pytest

from app.modules.audit.context import (
    AuditRuntimeContext,
    clear_audit_runtime_context,
    set_audit_runtime_context,
)
from app.modules.audit.hooks import audit_event_stub


@pytest.mark.asyncio
async def test_audit_logging_end_to_end():
    """Test the complete audit logging flow without a database.
    
    This test demonstrates:
    1. Setting up audit context (as middleware would do)
    2. Calling audit_event_stub from application code
    3. The stub silently returning when no session is available
    """
    # Simulate what middleware does - set up context
    tenant_id = uuid4()
    user_id = uuid4()
    
    ctx = AuditRuntimeContext(
        session=None,  # No session in this test
        tenant_id=tenant_id,
        actor_user_id=user_id,
        ip_address="192.168.1.100",
        user_agent="TestClient/1.0",
    )
    set_audit_runtime_context(ctx)
    
    try:
        # Simulate application code calling audit_event_stub
        # This should NOT crash even with no session
        await audit_event_stub(
            action="user.login",
            metadata={"method": "password"},
            resource_type="user",
            resource_id=str(user_id),
        )
        
        # If we get here, the test passed - no exception was raised
        assert True
        
        # Verify context is still available
        from app.modules.audit.context import get_audit_runtime_context
        retrieved_ctx = get_audit_runtime_context()
        assert retrieved_ctx is not None
        assert retrieved_ctx.tenant_id == tenant_id
        assert retrieved_ctx.actor_user_id == user_id
        
    finally:
        # Simulate what middleware does - clear context
        clear_audit_runtime_context()
    
    # After clearing, context should be None
    from app.modules.audit.context import get_audit_runtime_context
    assert get_audit_runtime_context() is None


@pytest.mark.asyncio
async def test_concurrent_audit_contexts():
    """Test that audit contexts don't interfere between concurrent requests."""
    
    async def simulate_request(request_id: int, tenant_id):
        """Simulate a single request with its own audit context."""
        ctx = AuditRuntimeContext(
            session=None,
            tenant_id=tenant_id,
            actor_user_id=uuid4(),
        )
        set_audit_runtime_context(ctx)
        
        # Simulate some async work
        await asyncio.sleep(0.01)
        
        # Call audit stub
        await audit_event_stub(
            action=f"request.{request_id}",
            metadata={"request_id": request_id},
        )
        
        # Verify our context is still correct
        from app.modules.audit.context import get_audit_runtime_context
        retrieved = get_audit_runtime_context()
        assert retrieved is not None
        assert retrieved.tenant_id == tenant_id
        
        clear_audit_runtime_context()
        return request_id
    
    # Run 5 concurrent "requests"
    tenant_ids = [uuid4() for _ in range(5)]
    results = await asyncio.gather(*[
        simulate_request(i, tid) 
        for i, tid in enumerate(tenant_ids)
    ])
    
    # All requests should complete successfully
    assert len(results) == 5
    assert results == [0, 1, 2, 3, 4]
