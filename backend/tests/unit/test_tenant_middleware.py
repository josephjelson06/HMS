import pytest
from uuid import uuid4
from unittest.mock import Mock, AsyncMock

from app.modules.tenant.middleware import TenantContextMiddleware
from app.modules.tenant.context import AuthContext, TenantType


class TestTenantContextMiddleware:
    """Test TenantContextMiddleware."""

    @pytest.mark.anyio
    async def test_middleware_with_valid_token_payload(self):
        """Test middleware resolves AuthContext from valid token_payload."""
        middleware = TenantContextMiddleware(app=Mock())
        
        user_id = uuid4()
        tenant_id = uuid4()
        
        request = Mock()
        request.state.token_payload = {
            "sub": str(user_id),
            "tenant_id": str(tenant_id),
            "user_type": "hotel",
            "roles": ["admin"],
        }
        
        call_next = AsyncMock(return_value=Mock())
        
        await middleware.dispatch(request, call_next)
        
        assert hasattr(request.state, "auth_context")
        assert request.state.auth_context is not None
        assert isinstance(request.state.auth_context, AuthContext)
        assert request.state.auth_context.user_id == user_id
        assert request.state.auth_context.tenant_id == tenant_id
        assert request.state.auth_context.tenant_type == TenantType.HOTEL
        assert call_next.called

    @pytest.mark.anyio
    async def test_middleware_with_none_token_payload(self):
        """Test middleware sets auth_context to None when token_payload is None."""
        middleware = TenantContextMiddleware(app=Mock())
        
        request = Mock()
        request.state.token_payload = None
        
        call_next = AsyncMock(return_value=Mock())
        
        await middleware.dispatch(request, call_next)
        
        assert hasattr(request.state, "auth_context")
        assert request.state.auth_context is None
        assert call_next.called

    @pytest.mark.anyio
    async def test_middleware_with_missing_token_payload(self):
        """Test middleware handles missing token_payload attribute."""
        middleware = TenantContextMiddleware(app=Mock())
        
        request = Mock(spec=["state"])
        request.state = Mock(spec=[])  # state without token_payload attribute
        
        call_next = AsyncMock(return_value=Mock())
        
        await middleware.dispatch(request, call_next)
        
        assert hasattr(request.state, "auth_context")
        assert request.state.auth_context is None
        assert call_next.called

    @pytest.mark.anyio
    async def test_middleware_with_impersonation(self):
        """Test middleware resolves impersonation context correctly."""
        middleware = TenantContextMiddleware(app=Mock())
        
        user_id = uuid4()
        tenant_id = uuid4()
        actor_id = uuid4()
        acting_as_id = uuid4()
        
        request = Mock()
        request.state.token_payload = {
            "sub": str(user_id),
            "tenant_id": str(tenant_id),
            "user_type": "hotel",
            "roles": ["admin"],
            "impersonation": {
                "actor_user_id": str(actor_id),
                "acting_as_user_id": str(acting_as_id),
            },
        }
        
        call_next = AsyncMock(return_value=Mock())
        
        await middleware.dispatch(request, call_next)
        
        assert request.state.auth_context is not None
        assert request.state.auth_context.is_impersonating is True
        assert request.state.auth_context.actor_user_id == actor_id
        assert request.state.auth_context.acting_as_user_id == acting_as_id
        assert request.state.auth_context.effective_user_id == acting_as_id
        assert call_next.called

    @pytest.mark.anyio
    async def test_middleware_with_platform_user(self):
        """Test middleware resolves platform user correctly."""
        middleware = TenantContextMiddleware(app=Mock())
        
        user_id = uuid4()
        
        request = Mock()
        request.state.token_payload = {
            "sub": str(user_id),
            "tenant_id": None,
            "user_type": "platform",
            "roles": ["super_admin"],
        }
        
        call_next = AsyncMock(return_value=Mock())
        
        await middleware.dispatch(request, call_next)
        
        assert request.state.auth_context is not None
        assert request.state.auth_context.user_id == user_id
        assert request.state.auth_context.tenant_id is None
        assert request.state.auth_context.tenant_type == TenantType.PLATFORM
        assert call_next.called

    @pytest.mark.anyio
    async def test_middleware_with_legacy_admin_user_type_maps_to_platform(self):
        """Legacy user_type='admin' should map to TenantType.PLATFORM during transition."""
        middleware = TenantContextMiddleware(app=Mock())

        user_id = uuid4()

        request = Mock()
        request.state.token_payload = {
            "sub": str(user_id),
            "tenant_id": None,
            "user_type": "admin",  # legacy value
            "roles": ["super_admin"],
        }

        call_next = AsyncMock(return_value=Mock())

        await middleware.dispatch(request, call_next)

        assert request.state.auth_context is not None
        assert request.state.auth_context.user_id == user_id
        assert request.state.auth_context.tenant_id is None
        assert request.state.auth_context.tenant_type == TenantType.PLATFORM
        assert call_next.called
