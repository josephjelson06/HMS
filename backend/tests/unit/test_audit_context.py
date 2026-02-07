"""Unit tests for audit module context management."""

import asyncio
from uuid import UUID, uuid4

import pytest

from app.modules.audit.context import (
    AuditRuntimeContext,
    clear_audit_runtime_context,
    get_audit_runtime_context,
    set_audit_runtime_context,
)


def test_set_and_get_audit_context():
    """Test setting and getting audit context in the same async context."""
    # Create a context
    ctx = AuditRuntimeContext(
        session=None,
        tenant_id=uuid4(),
        actor_user_id=uuid4(),
        acting_as_user_id=None,
        ip_address="192.168.1.1",
        user_agent="test-agent",
    )
    
    # Set it
    set_audit_runtime_context(ctx)
    
    # Get it back
    retrieved = get_audit_runtime_context()
    
    assert retrieved is not None
    assert retrieved.tenant_id == ctx.tenant_id
    assert retrieved.actor_user_id == ctx.actor_user_id
    assert retrieved.ip_address == "192.168.1.1"
    assert retrieved.user_agent == "test-agent"
    
    # Clean up
    clear_audit_runtime_context()


def test_clear_audit_context():
    """Test clearing audit context."""
    ctx = AuditRuntimeContext(
        session=None,
        tenant_id=uuid4(),
        actor_user_id=uuid4(),
    )
    
    set_audit_runtime_context(ctx)
    assert get_audit_runtime_context() is not None
    
    clear_audit_runtime_context()
    assert get_audit_runtime_context() is None


def test_context_isolation_between_tasks():
    """Test that audit context is isolated between async tasks."""
    results = []
    
    async def task_with_context(task_id: int):
        tenant_id = uuid4()
        ctx = AuditRuntimeContext(
            session=None,
            tenant_id=tenant_id,
            actor_user_id=uuid4(),
        )
        set_audit_runtime_context(ctx)
        
        # Simulate some async work
        await asyncio.sleep(0.01)
        
        # Verify context is still correct
        retrieved = get_audit_runtime_context()
        results.append((task_id, retrieved.tenant_id if retrieved else None))
        
        clear_audit_runtime_context()
    
    async def run_tasks():
        await asyncio.gather(
            task_with_context(1),
            task_with_context(2),
            task_with_context(3),
        )
    
    # Run the test
    asyncio.run(run_tasks())
    
    # Each task should have gotten its own context
    assert len(results) == 3
    # All should have different tenant_ids
    tenant_ids = [r[1] for r in results]
    assert len(set(tenant_ids)) == 3


def test_no_context_returns_none():
    """Test that getting context when none is set returns None."""
    clear_audit_runtime_context()
    assert get_audit_runtime_context() is None


def test_context_with_all_fields():
    """Test context with all fields populated."""
    tenant_id = uuid4()
    actor_id = uuid4()
    acting_as_id = uuid4()
    
    ctx = AuditRuntimeContext(
        session=None,
        tenant_id=tenant_id,
        actor_user_id=actor_id,
        acting_as_user_id=acting_as_id,
        ip_address="10.0.0.1",
        user_agent="Mozilla/5.0",
    )
    
    set_audit_runtime_context(ctx)
    retrieved = get_audit_runtime_context()
    
    assert retrieved is not None
    assert retrieved.tenant_id == tenant_id
    assert retrieved.actor_user_id == actor_id
    assert retrieved.acting_as_user_id == acting_as_id
    assert retrieved.ip_address == "10.0.0.1"
    assert retrieved.user_agent == "Mozilla/5.0"
    assert retrieved.session is None
    
    clear_audit_runtime_context()


def test_context_with_minimal_fields():
    """Test context with only required fields."""
    ctx = AuditRuntimeContext(
        session=None,
    )
    
    set_audit_runtime_context(ctx)
    retrieved = get_audit_runtime_context()
    
    assert retrieved is not None
    assert retrieved.tenant_id is None
    assert retrieved.actor_user_id is None
    assert retrieved.acting_as_user_id is None
    assert retrieved.ip_address is None
    assert retrieved.user_agent is None
    
    clear_audit_runtime_context()
