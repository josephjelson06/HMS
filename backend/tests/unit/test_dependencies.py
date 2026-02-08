import pytest
from unittest.mock import Mock, AsyncMock
from uuid import uuid4

from fastapi import HTTPException, Request

from app.modules.auth.dependencies import (
    require_tenant_permission,
    get_effective_permissions,
    CurrentUser,
)


@pytest.fixture
def mock_platform_user():
    """Create a mock platform user with permissions."""
    return CurrentUser(
        id=uuid4(),
        email="admin@platform.com",
        first_name="Platform",
        last_name="Admin",
        user_type="platform",
        tenant_id=None,
        roles=["platform_admin"],
        permissions=["platform:hotels:read", "platform:hotels:create", "platform:*"],
        impersonation=None,
    )


@pytest.fixture
def mock_hotel_user():
    """Create a mock hotel user with permissions."""
    return CurrentUser(
        id=uuid4(),
        email="manager@hotel.com",
        first_name="Hotel",
        last_name="Manager",
        user_type="hotel",
        tenant_id=uuid4(),
        roles=["hotel_manager"],
        permissions=["hotel:rooms:create", "hotel:rooms:read", "hotel:guests:*"],
        impersonation=None,
    )


@pytest.mark.asyncio
async def test_require_tenant_permission_hotel_user_with_permission(mock_hotel_user):
    """Test require_tenant_permission with hotel user who has the required permission."""
    checker = require_tenant_permission("rooms", "create")
    
    # Mock the get_current_user dependency
    async def mock_get_current_user():
        return mock_hotel_user
    
    # Call the dependency
    result = await checker(current_user=mock_hotel_user)
    
    # Should return the scoped permission that was checked
    assert result == "hotel:rooms:create"


@pytest.mark.asyncio
async def test_require_tenant_permission_platform_user_with_permission(mock_platform_user):
    """Test require_tenant_permission with platform user who has the required permission."""
    checker = require_tenant_permission("hotels", "read")
    
    # Call the dependency
    result = await checker(current_user=mock_platform_user)
    
    # Should return the scoped permission that was checked
    assert result == "platform:hotels:read"


@pytest.mark.asyncio
async def test_require_tenant_permission_hotel_user_with_wildcard(mock_hotel_user):
    """Test require_tenant_permission with hotel user who has wildcard permission."""
    checker = require_tenant_permission("guests", "create")
    
    # Call the dependency - user has "hotel:guests:*" which should match
    result = await checker(current_user=mock_hotel_user)
    
    assert result == "hotel:guests:create"


@pytest.mark.asyncio
async def test_require_tenant_permission_platform_user_with_wildcard(mock_platform_user):
    """Test require_tenant_permission with platform user who has wildcard permission."""
    checker = require_tenant_permission("users", "delete")
    
    # Call the dependency - user has "platform:*" which should match
    result = await checker(current_user=mock_platform_user)
    
    assert result == "platform:users:delete"


@pytest.mark.asyncio
async def test_require_tenant_permission_without_permission(mock_hotel_user):
    """Test require_tenant_permission with user lacking the required permission."""
    checker = require_tenant_permission("billing", "create")
    
    # User doesn't have hotel:billing:create permission
    with pytest.raises(HTTPException) as exc_info:
        await checker(current_user=mock_hotel_user)
    
    assert exc_info.value.status_code == 403
    assert "Permission denied: hotel:billing:create" in exc_info.value.detail


@pytest.mark.asyncio
async def test_get_effective_permissions_returns_frozenset(mock_hotel_user):
    """Test that get_effective_permissions returns a frozenset."""
    request = Mock(spec=Request)
    request.state = Mock()
    request.state._effective_permissions = None
    
    result = await get_effective_permissions(request, mock_hotel_user)
    
    assert isinstance(result, frozenset)
    assert "hotel:rooms:create" in result
    assert "hotel:rooms:read" in result
    assert "hotel:guests:*" in result


@pytest.mark.asyncio
async def test_get_effective_permissions_caching(mock_hotel_user):
    """Test that get_effective_permissions caches results per request."""
    request = Mock(spec=Request)
    request.state = Mock()
    
    # First call - should compute and cache
    result1 = await get_effective_permissions(request, mock_hotel_user)
    
    # Second call - should return cached value
    result2 = await get_effective_permissions(request, mock_hotel_user)
    
    # Should be the same object (cached)
    assert result1 is result2
    assert result1 == result2
