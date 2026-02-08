import pytest
from uuid import UUID, uuid4
from dataclasses import FrozenInstanceError

from app.modules.tenant.context import (
    AuthContext,
    TenantType,
    resolve_auth_context_from_claims,
)


class TestTenantType:
    """Test TenantType enum."""

    def test_platform_value(self):
        assert TenantType.PLATFORM.value == "platform"

    def test_hotel_value(self):
        assert TenantType.HOTEL.value == "hotel"


class TestAuthContext:
    """Test AuthContext dataclass."""

    def test_auth_context_basic(self):
        """Test basic AuthContext creation."""
        tenant_id = uuid4()
        user_id = uuid4()
        roles = ("admin", "user")

        context = AuthContext(
            tenant_id=tenant_id,
            tenant_type=TenantType.HOTEL,
            user_id=user_id,
            roles=roles,
        )

        assert context.tenant_id == tenant_id
        assert context.tenant_type == TenantType.HOTEL
        assert context.user_id == user_id
        assert context.roles == roles
        assert context.actor_user_id is None
        assert context.acting_as_user_id is None

    def test_auth_context_frozen(self):
        """Test that AuthContext is frozen (immutable)."""
        context = AuthContext(
            tenant_id=uuid4(),
            tenant_type=TenantType.HOTEL,
            user_id=uuid4(),
            roles=("admin",),
        )

        with pytest.raises(FrozenInstanceError):
            context.tenant_id = uuid4()

        with pytest.raises(FrozenInstanceError):
            context.user_id = uuid4()

    def test_is_impersonating_false(self):
        """Test is_impersonating returns False when not impersonating."""
        context = AuthContext(
            tenant_id=uuid4(),
            tenant_type=TenantType.HOTEL,
            user_id=uuid4(),
            roles=("admin",),
        )

        assert context.is_impersonating is False

    def test_is_impersonating_true(self):
        """Test is_impersonating returns True when impersonating."""
        context = AuthContext(
            tenant_id=uuid4(),
            tenant_type=TenantType.HOTEL,
            user_id=uuid4(),
            roles=("admin",),
            actor_user_id=uuid4(),
            acting_as_user_id=uuid4(),
        )

        assert context.is_impersonating is True

    def test_is_impersonating_partial_false(self):
        """Test is_impersonating returns False when only one impersonation field is set."""
        context1 = AuthContext(
            tenant_id=uuid4(),
            tenant_type=TenantType.HOTEL,
            user_id=uuid4(),
            roles=("admin",),
            actor_user_id=uuid4(),
            acting_as_user_id=None,
        )
        assert context1.is_impersonating is False

        context2 = AuthContext(
            tenant_id=uuid4(),
            tenant_type=TenantType.HOTEL,
            user_id=uuid4(),
            roles=("admin",),
            actor_user_id=None,
            acting_as_user_id=uuid4(),
        )
        assert context2.is_impersonating is False

    def test_effective_user_id_normal(self):
        """Test effective_user_id returns user_id when not impersonating."""
        user_id = uuid4()
        context = AuthContext(
            tenant_id=uuid4(),
            tenant_type=TenantType.HOTEL,
            user_id=user_id,
            roles=("admin",),
        )

        assert context.effective_user_id == user_id

    def test_effective_user_id_impersonation(self):
        """Test effective_user_id returns acting_as_user_id during impersonation."""
        user_id = uuid4()
        acting_as_id = uuid4()
        context = AuthContext(
            tenant_id=uuid4(),
            tenant_type=TenantType.HOTEL,
            user_id=user_id,
            roles=("admin",),
            actor_user_id=uuid4(),
            acting_as_user_id=acting_as_id,
        )

        assert context.effective_user_id == acting_as_id
        assert context.effective_user_id != user_id

    def test_effective_user_id_none(self):
        """Test effective_user_id returns None when both user_id and acting_as_user_id are None."""
        context = AuthContext(
            tenant_id=uuid4(),
            tenant_type=TenantType.HOTEL,
            user_id=None,
            roles=("admin",),
        )

        assert context.effective_user_id is None


class TestResolveAuthContextFromClaims:
    """Test resolve_auth_context_from_claims function."""

    def test_resolve_from_none_claims(self):
        """Test that None claims return None."""
        result = resolve_auth_context_from_claims(None)
        assert result is None

    def test_resolve_basic_claims(self):
        """Test resolving AuthContext from basic claims."""
        tenant_id = uuid4()
        user_id = uuid4()
        claims = {
            "sub": str(user_id),
            "tenant_id": str(tenant_id),
            "user_type": "hotel",
            "roles": ["admin", "user"],
        }

        context = resolve_auth_context_from_claims(claims)

        assert context is not None
        assert context.user_id == user_id
        assert context.tenant_id == tenant_id
        assert context.tenant_type == TenantType.HOTEL
        assert context.roles == ("admin", "user")
        assert context.actor_user_id is None
        assert context.acting_as_user_id is None

    def test_resolve_platform_user(self):
        """Test resolving AuthContext for platform user."""
        user_id = uuid4()
        claims = {
            "sub": str(user_id),
            "tenant_id": None,
            "user_type": "platform",
            "roles": ["super_admin"],
        }

        context = resolve_auth_context_from_claims(claims)

        assert context is not None
        assert context.user_id == user_id
        assert context.tenant_id is None
        assert context.tenant_type == TenantType.PLATFORM
        assert context.roles == ("super_admin",)

    def test_resolve_with_impersonation(self):
        """Test resolving AuthContext with impersonation."""
        user_id = uuid4()
        tenant_id = uuid4()
        actor_id = uuid4()
        acting_as_id = uuid4()

        claims = {
            "sub": str(user_id),
            "tenant_id": str(tenant_id),
            "user_type": "hotel",
            "roles": ["admin"],
            "impersonation": {
                "actor_user_id": str(actor_id),
                "acting_as_user_id": str(acting_as_id),
            },
        }

        context = resolve_auth_context_from_claims(claims)

        assert context is not None
        assert context.user_id == user_id
        assert context.actor_user_id == actor_id
        assert context.acting_as_user_id == acting_as_id
        assert context.is_impersonating is True
        assert context.effective_user_id == acting_as_id

    def test_resolve_fallback_tenant_type(self):
        """Test that invalid user_type falls back to HOTEL."""
        claims = {
            "sub": str(uuid4()),
            "user_type": "invalid_type",
            "roles": [],
        }

        context = resolve_auth_context_from_claims(claims)

        assert context is not None
        assert context.tenant_type == TenantType.HOTEL

    def test_resolve_missing_user_type(self):
        """Test that missing user_type defaults to HOTEL."""
        claims = {
            "sub": str(uuid4()),
            "roles": [],
        }

        context = resolve_auth_context_from_claims(claims)

        assert context is not None
        assert context.tenant_type == TenantType.HOTEL

    def test_resolve_empty_roles(self):
        """Test resolving with empty roles list."""
        claims = {
            "sub": str(uuid4()),
            "user_type": "hotel",
            "roles": [],
        }

        context = resolve_auth_context_from_claims(claims)

        assert context is not None
        assert context.roles == ()

    def test_resolve_missing_roles(self):
        """Test resolving with missing roles field."""
        claims = {
            "sub": str(uuid4()),
            "user_type": "hotel",
        }

        context = resolve_auth_context_from_claims(claims)

        assert context is not None
        assert context.roles == ()

    def test_resolve_roles_as_tuple(self):
        """Test resolving when roles is already a tuple."""
        claims = {
            "sub": str(uuid4()),
            "user_type": "hotel",
            "roles": ("admin", "user"),
        }

        context = resolve_auth_context_from_claims(claims)

        assert context is not None
        assert context.roles == ("admin", "user")

    def test_resolve_missing_tenant_id(self):
        """Test resolving without tenant_id."""
        claims = {
            "sub": str(uuid4()),
            "user_type": "platform",
            "roles": ["super_admin"],
        }

        context = resolve_auth_context_from_claims(claims)

        assert context is not None
        assert context.tenant_id is None

    def test_resolve_missing_user_id(self):
        """Test resolving without user_id (sub claim)."""
        claims = {
            "user_type": "hotel",
            "roles": [],
        }

        context = resolve_auth_context_from_claims(claims)

        assert context is not None
        assert context.user_id is None

    def test_resolve_impersonation_not_dict(self):
        """Test resolving when impersonation is not a dict."""
        claims = {
            "sub": str(uuid4()),
            "user_type": "hotel",
            "roles": [],
            "impersonation": "not_a_dict",
        }

        context = resolve_auth_context_from_claims(claims)

        assert context is not None
        assert context.actor_user_id is None
        assert context.acting_as_user_id is None

    def test_resolve_partial_impersonation(self):
        """Test resolving with partial impersonation data."""
        claims = {
            "sub": str(uuid4()),
            "user_type": "hotel",
            "roles": [],
            "impersonation": {
                "actor_user_id": str(uuid4()),
                # missing acting_as_user_id
            },
        }

        context = resolve_auth_context_from_claims(claims)

        assert context is not None
        assert context.actor_user_id is not None
        assert context.acting_as_user_id is None
        assert context.is_impersonating is False
