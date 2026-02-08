"""Tests for refresh token family system."""
import pytest
from uuid import uuid4
from datetime import datetime, UTC, timedelta

from app.modules.auth.refresh_tokens import (
    build_refresh_token,
    hash_refresh_token,
    parse_tenant_id_from_refresh_token,
    RefreshTokenError,
    RefreshTokenReuseDetectedError,
    issue_new_refresh_token_family,
    rotate_refresh_token,
    revoke_family_by_refresh_token,
    revoke_refresh_token_family,
    revoke_all_refresh_token_families,
)


class TestTokenFormat:
    """Test token format functions."""
    
    def test_build_refresh_token(self):
        """Test building a structured refresh token."""
        tenant_id = uuid4()
        token = build_refresh_token(tenant_id)
        
        # Should have format: rt1.{uuid}.{random}
        parts = token.split(".")
        assert len(parts) == 3
        assert parts[0] == "rt1"
        assert parts[1] == str(tenant_id)
        assert len(parts[2]) > 0
    
    def test_hash_refresh_token(self):
        """Test hashing a refresh token."""
        token = "rt1.test.token"
        hash1 = hash_refresh_token(token)
        hash2 = hash_refresh_token(token)
        
        # Same token should produce same hash
        assert hash1 == hash2
        # Hash should be 64 chars (SHA-256 hex)
        assert len(hash1) == 64
    
    def test_parse_tenant_id_from_refresh_token(self):
        """Test extracting tenant_id from token."""
        tenant_id = uuid4()
        token = build_refresh_token(tenant_id)
        
        parsed = parse_tenant_id_from_refresh_token(token)
        assert parsed == tenant_id
    
    def test_parse_tenant_id_invalid_format(self):
        """Test parsing invalid token format."""
        with pytest.raises(RefreshTokenError) as exc:
            parse_tenant_id_from_refresh_token("invalid")
        assert "format is invalid" in str(exc.value)
    
    def test_parse_tenant_id_invalid_uuid(self):
        """Test parsing token with malformed UUID."""
        with pytest.raises(RefreshTokenError) as exc:
            parse_tenant_id_from_refresh_token("rt1.not-a-uuid.random")
        assert "malformed" in str(exc.value)
    
    def test_parse_tenant_id_wrong_version(self):
        """Test parsing token with wrong version."""
        with pytest.raises(RefreshTokenError) as exc:
            parse_tenant_id_from_refresh_token("rt2.uuid.random")
        assert "format is invalid" in str(exc.value)


# Mock session for testing - in real tests, you'd use a test database
class MockAsyncSession:
    """Mock session for unit tests."""
    def __init__(self):
        self.families = {}
        self.tokens = {}
        self.committed = False
    
    def add(self, obj):
        if hasattr(obj, '__tablename__'):
            if obj.__tablename__ == 'refresh_token_families':
                if not hasattr(obj, 'id') or obj.id is None:
                    obj.id = uuid4()
                self.families[obj.id] = obj
            elif obj.__tablename__ == 'refresh_tokens':
                if not hasattr(obj, 'id') or obj.id is None:
                    obj.id = uuid4()
                self.tokens[obj.id] = obj
    
    async def flush(self):
        pass
    
    async def commit(self):
        self.committed = True
    
    async def execute(self, stmt):
        # Mock execute for queries
        return MockResult([])


class MockResult:
    """Mock result for queries."""
    def __init__(self, data):
        self._data = data
    
    def scalar_one_or_none(self):
        return self._data[0] if self._data else None
    
    def scalars(self):
        return self
    
    def all(self):
        return self._data


class TestRefreshTokenFamilySystem:
    """Integration-style tests for the family system (using mocks)."""
    
    @pytest.mark.asyncio
    async def test_issue_new_family(self):
        """Test creating a new token family."""
        session = MockAsyncSession()
        tenant_id = uuid4()
        user_id = uuid4()
        
        result = await issue_new_refresh_token_family(
            session,
            tenant_id=tenant_id,
            user_id=user_id,
            refresh_token_days=30,
            created_by_user_id=user_id,
        )
        
        # Should return structured result
        assert result.raw_token.startswith("rt1.")
        assert result.family_id is not None
        assert result.token_id is not None
        
        # Should have created family and token
        assert result.family_id in session.families
        assert result.token_id in session.tokens
        
        # Token should belong to family
        token = session.tokens[result.token_id]
        assert token.family_id == result.family_id
    
    @pytest.mark.asyncio
    async def test_token_structure(self):
        """Test that issued tokens have correct structure."""
        session = MockAsyncSession()
        tenant_id = uuid4()
        user_id = uuid4()
        
        result = await issue_new_refresh_token_family(
            session,
            tenant_id=tenant_id,
            user_id=user_id,
            refresh_token_days=30,
        )
        
        # Verify we can parse tenant back out
        parsed_tenant = parse_tenant_id_from_refresh_token(result.raw_token)
        assert parsed_tenant == tenant_id


def test_token_uniqueness():
    """Test that tokens are unique even for same tenant."""
    tenant_id = uuid4()
    token1 = build_refresh_token(tenant_id)
    token2 = build_refresh_token(tenant_id)
    
    assert token1 != token2
    
    # But both should have same tenant
    assert parse_tenant_id_from_refresh_token(token1) == tenant_id
    assert parse_tenant_id_from_refresh_token(token2) == tenant_id


def test_exception_hierarchy():
    """Test that custom exceptions work correctly."""
    # RefreshTokenReuseDetectedError should be a RefreshTokenError
    exc = RefreshTokenReuseDetectedError()
    assert isinstance(exc, RefreshTokenError)
    assert exc.status_code == 401
    assert "reuse detected" in exc.detail.lower()
    
    # Generic RefreshTokenError
    exc2 = RefreshTokenError("Test error", status_code=400)
    assert exc2.status_code == 400
    assert exc2.detail == "Test error"


@pytest.mark.asyncio
async def test_revoke_refresh_token_family_delegates_to_internal(monkeypatch):
    """Test explicit family revoke helper delegates to internal family revocation."""
    captured = {}

    async def fake_revoke_family(session, *, family_id, reason):
        captured["session"] = session
        captured["family_id"] = family_id
        captured["reason"] = reason
        return 7

    monkeypatch.setattr("app.modules.auth.refresh_tokens._revoke_family", fake_revoke_family)

    session = object()
    family_id = uuid4()
    revoked_count = await revoke_refresh_token_family(
        session,
        family_id=family_id,
        reason="impersonation_ended",
    )

    assert revoked_count == 7
    assert captured["session"] is session
    assert captured["family_id"] == family_id
    assert captured["reason"] == "impersonation_ended"
