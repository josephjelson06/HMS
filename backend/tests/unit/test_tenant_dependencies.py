import pytest
from uuid import uuid4
from unittest.mock import Mock
from fastapi import HTTPException

from app.modules.tenant.context import AuthContext, TenantType
from app.modules.tenant.dependencies import (
    require_auth_context,
    require_authenticated_user_id,
)


class TestRequireAuthContext:
    """Test require_auth_context dependency."""

    @pytest.mark.anyio
    async def test_require_auth_context_success(self):
        """Test that require_auth_context returns AuthContext when available."""
        request = Mock()
        auth_context = AuthContext(
            tenant_id=uuid4(),
            tenant_type=TenantType.HOTEL,
            user_id=uuid4(),
            roles=("admin",),
        )
        request.state.auth_context = auth_context

        result = await require_auth_context(request)

        assert result is auth_context

    @pytest.mark.anyio
    async def test_require_auth_context_none(self):
        """Test that require_auth_context raises 401 when auth_context is None."""
        request = Mock()
        request.state.auth_context = None

        with pytest.raises(HTTPException) as exc_info:
            await require_auth_context(request)

        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Authentication required."

    @pytest.mark.anyio
    async def test_require_auth_context_missing_attribute(self):
        """Test that require_auth_context raises 401 when auth_context attribute doesn't exist."""
        request = Mock(spec=["state"])
        request.state = Mock(spec=[])  # state with no auth_context attribute

        with pytest.raises(HTTPException) as exc_info:
            await require_auth_context(request)

        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Authentication required."


class TestRequireAuthenticatedUserId:
    """Test require_authenticated_user_id dependency."""

    @pytest.mark.anyio
    async def test_require_user_id_success(self):
        """Test that require_authenticated_user_id returns user_id when available."""
        user_id = uuid4()
        auth_context = AuthContext(
            tenant_id=uuid4(),
            tenant_type=TenantType.HOTEL,
            user_id=user_id,
            roles=("admin",),
        )

        result = await require_authenticated_user_id(auth_context)

        assert result == user_id

    @pytest.mark.anyio
    async def test_require_user_id_impersonation(self):
        """Test that require_authenticated_user_id returns acting_as_user_id during impersonation."""
        user_id = uuid4()
        acting_as_id = uuid4()
        auth_context = AuthContext(
            tenant_id=uuid4(),
            tenant_type=TenantType.HOTEL,
            user_id=user_id,
            roles=("admin",),
            actor_user_id=uuid4(),
            acting_as_user_id=acting_as_id,
        )

        result = await require_authenticated_user_id(auth_context)

        assert result == acting_as_id
        assert result != user_id

    @pytest.mark.anyio
    async def test_require_user_id_none(self):
        """Test that require_authenticated_user_id raises 401 when user_id is None."""
        auth_context = AuthContext(
            tenant_id=uuid4(),
            tenant_type=TenantType.HOTEL,
            user_id=None,
            roles=("admin",),
        )

        with pytest.raises(HTTPException) as exc_info:
            await require_authenticated_user_id(auth_context)

        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Authenticated user ID is required."
