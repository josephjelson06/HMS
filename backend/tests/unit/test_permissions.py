import pytest

from app.core.permissions import (
    has_permission,
    validate_permission_key,
    permission_implies,
    ensure_role_scope_match,
    build_scoped_permission,
)


def test_exact_match():
    assert has_permission(["hotel:guests:create"], "hotel:guests:create")


def test_wildcard_scope():
    assert has_permission(["hotel:guests:*"], "hotel:guests:create")


def test_wildcard_all():
    assert has_permission(["hotel:*:*"], "hotel:rooms:update")


def test_no_match():
    assert not has_permission(["hotel:guests:read"], "hotel:guests:create")


# --- Tests for new AuthModule functions ---


def test_validate_permission_key_valid():
    """Test validation of valid permission keys."""
    assert validate_permission_key("hotel:rooms:create") == "hotel:rooms:create"
    assert validate_permission_key("platform:users:read") == "platform:users:read"
    assert validate_permission_key("hotel:*") == "hotel:*"
    assert validate_permission_key("platform:hotels:*") == "platform:hotels:*"
    assert validate_permission_key("a:b:c") == "a:b:c"
    assert validate_permission_key("hotel_admin:rooms:create") == "hotel_admin:rooms:create"


def test_validate_permission_key_invalid():
    """Test validation of invalid permission keys."""
    with pytest.raises(ValueError, match="does not match the required pattern"):
        validate_permission_key("Hotel:Rooms")
    
    with pytest.raises(ValueError, match="does not match the required pattern"):
        validate_permission_key("123:abc")
    
    with pytest.raises(ValueError, match="does not match the required pattern"):
        validate_permission_key("")
    
    with pytest.raises(ValueError, match="does not match the required pattern"):
        validate_permission_key("hotel rooms create")
    
    with pytest.raises(ValueError, match="does not match the required pattern"):
        validate_permission_key("HOTEL:ROOMS:CREATE")


def test_permission_implies():
    """Test permission_implies wrapper function."""
    assert permission_implies("hotel:rooms:*", "hotel:rooms:create")
    assert permission_implies("hotel:*", "hotel:rooms:create")
    assert permission_implies("hotel:rooms:create", "hotel:rooms:create")
    assert not permission_implies("hotel:rooms:read", "hotel:rooms:create")


def test_ensure_role_scope_match_valid():
    """Test role scope matching with valid combinations."""
    # Platform roles on platform tenant
    ensure_role_scope_match("platform_super_admin", "platform")
    ensure_role_scope_match("platform_admin", "platform")
    
    # Hotel roles on hotel tenant
    ensure_role_scope_match("hotel_admin", "hotel")
    ensure_role_scope_match("hotel_manager", "hotel")
    ensure_role_scope_match("hotel_front_desk", "hotel")
    ensure_role_scope_match("hotel_housekeeping", "hotel")
    ensure_role_scope_match("hotel_maintenance", "hotel")
    ensure_role_scope_match("hotel_auditor", "hotel")


def test_ensure_role_scope_match_invalid_platform_on_hotel():
    """Test that platform roles cannot be assigned to hotel tenants."""
    with pytest.raises(ValueError, match="platform role and cannot be assigned in a 'hotel' tenant"):
        ensure_role_scope_match("platform_admin", "hotel")
    
    with pytest.raises(ValueError, match="platform role and cannot be assigned in a 'hotel' tenant"):
        ensure_role_scope_match("platform_super_admin", "hotel")


def test_ensure_role_scope_match_invalid_hotel_on_platform():
    """Test that hotel roles cannot be assigned to platform tenants."""
    with pytest.raises(ValueError, match="hotel role and cannot be assigned in a 'platform' tenant"):
        ensure_role_scope_match("hotel_admin", "platform")
    
    with pytest.raises(ValueError, match="hotel role and cannot be assigned in a 'platform' tenant"):
        ensure_role_scope_match("hotel_manager", "platform")


def test_build_scoped_permission():
    """Test building scoped permission strings."""
    assert build_scoped_permission("platform", "hotels", "read") == "platform:hotels:read"
    assert build_scoped_permission("hotel", "rooms", "create") == "hotel:rooms:create"
    assert build_scoped_permission("platform", "users", "delete") == "platform:users:delete"
    assert build_scoped_permission("hotel", "guests", "update") == "hotel:guests:update"
