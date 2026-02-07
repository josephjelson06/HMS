import pytest
from datetime import datetime, timedelta, UTC
from uuid import uuid4, UUID

from app.modules.auth.tokens import (
    AccessTokenClaims,
    AccessTokenError,
    create_access_token,
    decode_access_token,
)
from app.core.config import settings


def test_create_access_token_basic():
    """Test creating a basic access token with required fields."""
    user_id = uuid4()
    user_type = "admin"
    roles = ["admin"]

    token, claims = create_access_token(
        user_id=user_id,
        user_type=user_type,
        roles=roles,
    )

    assert isinstance(token, str)
    assert isinstance(claims, AccessTokenClaims)
    assert claims.user_id == user_id
    assert claims.user_type == user_type
    assert claims.roles == tuple(roles)
    assert isinstance(claims.jti, UUID)
    assert isinstance(claims.issued_at, datetime)
    assert isinstance(claims.expires_at, datetime)
    assert claims.tenant_id is None
    assert claims.actor_user_id is None
    assert claims.acting_as_user_id is None


def test_create_access_token_with_tenant():
    """Test creating an access token with tenant_id."""
    user_id = uuid4()
    tenant_id = uuid4()
    user_type = "hotel"
    roles = ["manager"]

    token, claims = create_access_token(
        user_id=user_id,
        user_type=user_type,
        roles=roles,
        tenant_id=tenant_id,
    )

    assert claims.tenant_id == tenant_id


def test_create_access_token_with_impersonation():
    """Test creating an access token with impersonation data."""
    user_id = uuid4()
    actor_user_id = uuid4()
    acting_as_user_id = uuid4()
    user_type = "hotel"
    roles = ["manager"]

    token, claims = create_access_token(
        user_id=user_id,
        user_type=user_type,
        roles=roles,
        actor_user_id=actor_user_id,
        acting_as_user_id=acting_as_user_id,
    )

    assert claims.actor_user_id == actor_user_id
    assert claims.acting_as_user_id == acting_as_user_id


def test_create_access_token_custom_expiry():
    """Test creating an access token with custom expiry."""
    user_id = uuid4()
    user_type = "admin"
    roles = ["admin"]
    custom_delta = timedelta(minutes=60)

    token, claims = create_access_token(
        user_id=user_id,
        user_type=user_type,
        roles=roles,
        expires_delta=custom_delta,
    )

    expected_duration = custom_delta.total_seconds()
    actual_duration = (claims.expires_at - claims.issued_at).total_seconds()
    # Allow for small timing differences
    assert abs(actual_duration - expected_duration) < 2


def test_decode_access_token_valid():
    """Test decoding a valid access token."""
    user_id = uuid4()
    user_type = "admin"
    roles = ["admin", "user"]

    token, original_claims = create_access_token(
        user_id=user_id,
        user_type=user_type,
        roles=roles,
    )

    decoded_claims = decode_access_token(token)

    assert decoded_claims.user_id == original_claims.user_id
    assert decoded_claims.user_type == original_claims.user_type
    assert decoded_claims.roles == original_claims.roles
    assert decoded_claims.jti == original_claims.jti
    assert decoded_claims.tenant_id == original_claims.tenant_id
    assert decoded_claims.actor_user_id == original_claims.actor_user_id
    assert decoded_claims.acting_as_user_id == original_claims.acting_as_user_id


def test_decode_access_token_with_all_fields():
    """Test decoding an access token with all optional fields."""
    user_id = uuid4()
    tenant_id = uuid4()
    actor_user_id = uuid4()
    acting_as_user_id = uuid4()
    user_type = "hotel"
    roles = ["manager"]

    token, original_claims = create_access_token(
        user_id=user_id,
        user_type=user_type,
        roles=roles,
        tenant_id=tenant_id,
        actor_user_id=actor_user_id,
        acting_as_user_id=acting_as_user_id,
    )

    decoded_claims = decode_access_token(token)

    assert decoded_claims.user_id == user_id
    assert decoded_claims.tenant_id == tenant_id
    assert decoded_claims.actor_user_id == actor_user_id
    assert decoded_claims.acting_as_user_id == acting_as_user_id


def test_decode_access_token_invalid_signature():
    """Test that decoding a token with invalid signature raises AccessTokenError."""
    with pytest.raises(AccessTokenError, match="Invalid or expired access token"):
        decode_access_token("invalid.token.signature")


def test_decode_access_token_expired():
    """Test that decoding an expired token raises AccessTokenError."""
    user_id = uuid4()
    user_type = "admin"
    roles = ["admin"]

    # Create a token that expires immediately
    token, _ = create_access_token(
        user_id=user_id,
        user_type=user_type,
        roles=roles,
        expires_delta=timedelta(seconds=-1),  # Already expired
    )

    with pytest.raises(AccessTokenError, match="Invalid or expired access token"):
        decode_access_token(token)


def test_decode_access_token_missing_sub():
    """Test that a token missing 'sub' claim raises AccessTokenError."""
    import jwt
    
    payload = {
        "user_type": "admin",
        "roles": ["admin"],
        "jti": str(uuid4()),
        "iat": int(datetime.now(UTC).timestamp()),
        "exp": int((datetime.now(UTC) + timedelta(minutes=15)).timestamp()),
    }
    token = jwt.encode(payload, settings.jwt_secret, algorithm="HS256")

    with pytest.raises(AccessTokenError, match="Invalid or expired access token"):
        decode_access_token(token)


def test_decode_access_token_missing_roles():
    """Test that a token missing 'roles' claim raises AccessTokenError."""
    import jwt
    
    payload = {
        "sub": str(uuid4()),
        "user_type": "admin",
        "jti": str(uuid4()),
        "iat": int(datetime.now(UTC).timestamp()),
        "exp": int((datetime.now(UTC) + timedelta(minutes=15)).timestamp()),
    }
    token = jwt.encode(payload, settings.jwt_secret, algorithm="HS256")

    with pytest.raises(AccessTokenError, match="Invalid or expired access token"):
        decode_access_token(token)


def test_decode_access_token_invalid_uuid():
    """Test that a token with invalid UUID raises AccessTokenError."""
    import jwt
    
    payload = {
        "sub": "not-a-uuid",
        "user_type": "admin",
        "roles": ["admin"],
        "jti": str(uuid4()),
        "iat": int(datetime.now(UTC).timestamp()),
        "exp": int((datetime.now(UTC) + timedelta(minutes=15)).timestamp()),
    }
    token = jwt.encode(payload, settings.jwt_secret, algorithm="HS256")

    with pytest.raises(AccessTokenError, match="Access token payload is malformed"):
        decode_access_token(token)


def test_decode_access_token_roles_not_list():
    """Test that a token with roles as non-list raises AccessTokenError."""
    import jwt
    
    payload = {
        "sub": str(uuid4()),
        "user_type": "admin",
        "roles": "admin",  # Should be a list
        "jti": str(uuid4()),
        "iat": int(datetime.now(UTC).timestamp()),
        "exp": int((datetime.now(UTC) + timedelta(minutes=15)).timestamp()),
    }
    token = jwt.encode(payload, settings.jwt_secret, algorithm="HS256")

    with pytest.raises(AccessTokenError, match="Access token payload is malformed"):
        decode_access_token(token)


def test_decode_access_token_roles_not_strings():
    """Test that a token with roles containing non-strings raises AccessTokenError."""
    import jwt
    
    payload = {
        "sub": str(uuid4()),
        "user_type": "admin",
        "roles": ["admin", 123],  # Contains non-string
        "jti": str(uuid4()),
        "iat": int(datetime.now(UTC).timestamp()),
        "exp": int((datetime.now(UTC) + timedelta(minutes=15)).timestamp()),
    }
    token = jwt.encode(payload, settings.jwt_secret, algorithm="HS256")

    with pytest.raises(AccessTokenError, match="Access token payload is malformed"):
        decode_access_token(token)


def test_decode_access_token_invalid_tenant_id():
    """Test that a token with invalid tenant_id raises AccessTokenError."""
    import jwt
    
    payload = {
        "sub": str(uuid4()),
        "user_type": "hotel",
        "roles": ["manager"],
        "jti": str(uuid4()),
        "iat": int(datetime.now(UTC).timestamp()),
        "exp": int((datetime.now(UTC) + timedelta(minutes=15)).timestamp()),
        "tenant_id": "not-a-uuid",
    }
    token = jwt.encode(payload, settings.jwt_secret, algorithm="HS256")

    with pytest.raises(AccessTokenError, match="Access token tenant_id is malformed"):
        decode_access_token(token)


def test_decode_access_token_invalid_impersonation_format():
    """Test that a token with invalid impersonation format raises AccessTokenError."""
    import jwt
    
    payload = {
        "sub": str(uuid4()),
        "user_type": "hotel",
        "roles": ["manager"],
        "jti": str(uuid4()),
        "iat": int(datetime.now(UTC).timestamp()),
        "exp": int((datetime.now(UTC) + timedelta(minutes=15)).timestamp()),
        "impersonation": "not-a-dict",
    }
    token = jwt.encode(payload, settings.jwt_secret, algorithm="HS256")

    with pytest.raises(AccessTokenError, match="Access token impersonation payload is malformed"):
        decode_access_token(token)


def test_decode_access_token_invalid_impersonation_ids():
    """Test that a token with invalid impersonation IDs raises AccessTokenError."""
    import jwt
    
    payload = {
        "sub": str(uuid4()),
        "user_type": "hotel",
        "roles": ["manager"],
        "jti": str(uuid4()),
        "iat": int(datetime.now(UTC).timestamp()),
        "exp": int((datetime.now(UTC) + timedelta(minutes=15)).timestamp()),
        "impersonation": {
            "actor_user_id": "not-a-uuid",
            "acting_as_user_id": str(uuid4()),
        },
    }
    token = jwt.encode(payload, settings.jwt_secret, algorithm="HS256")

    with pytest.raises(AccessTokenError, match="Access token impersonation IDs are malformed"):
        decode_access_token(token)


def test_effective_user_id_without_impersonation():
    """Test that effective_user_id returns user_id when not impersonating."""
    user_id = uuid4()
    claims = AccessTokenClaims(
        user_id=user_id,
        user_type="admin",
        roles=tuple(["admin"]),
        jti=uuid4(),
        issued_at=datetime.now(UTC),
        expires_at=datetime.now(UTC) + timedelta(minutes=15),
    )

    assert claims.effective_user_id == user_id


def test_effective_user_id_with_impersonation():
    """Test that effective_user_id returns acting_as_user_id when impersonating."""
    user_id = uuid4()
    acting_as_user_id = uuid4()
    claims = AccessTokenClaims(
        user_id=user_id,
        user_type="hotel",
        roles=tuple(["manager"]),
        jti=uuid4(),
        issued_at=datetime.now(UTC),
        expires_at=datetime.now(UTC) + timedelta(minutes=15),
        actor_user_id=uuid4(),
        acting_as_user_id=acting_as_user_id,
    )

    assert claims.effective_user_id == acting_as_user_id


def test_access_token_claims_is_frozen():
    """Test that AccessTokenClaims is immutable (frozen)."""
    claims = AccessTokenClaims(
        user_id=uuid4(),
        user_type="admin",
        roles=tuple(["admin"]),
        jti=uuid4(),
        issued_at=datetime.now(UTC),
        expires_at=datetime.now(UTC) + timedelta(minutes=15),
    )

    with pytest.raises(AttributeError):
        claims.user_id = uuid4()


def test_roles_converted_to_tuple():
    """Test that roles are converted from list to tuple in AccessTokenClaims."""
    user_id = uuid4()
    roles_list = ["admin", "user"]

    token, claims = create_access_token(
        user_id=user_id,
        user_type="admin",
        roles=roles_list,
    )

    assert isinstance(claims.roles, tuple)
    assert claims.roles == tuple(roles_list)
