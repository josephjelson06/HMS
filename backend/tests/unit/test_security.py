"""Unit tests for security functions."""
import time
import pytest

from app.core.security import (
    hash_password,
    verify_password,
    verify_password_constant_time,
    create_access_token,
    decode_access_token,
)


class TestPasswordHashing:
    """Test password hashing and verification."""

    def test_hash_password_creates_valid_bcrypt_hash(self):
        """Test that hash_password creates a valid bcrypt hash."""
        password = "test_password_123"
        hashed = hash_password(password)
        
        # Bcrypt hashes start with $2b$ and are 60 characters
        assert hashed.startswith("$2b$")
        assert len(hashed) == 60

    def test_verify_password_with_correct_password(self):
        """Test that verify_password returns True for correct password."""
        password = "correct_password"
        hashed = hash_password(password)
        
        assert verify_password(password, hashed) is True

    def test_verify_password_with_wrong_password(self):
        """Test that verify_password returns False for wrong password."""
        password = "correct_password"
        wrong_password = "wrong_password"
        hashed = hash_password(password)
        
        assert verify_password(wrong_password, hashed) is False


class TestConstantTimeVerification:
    """Test constant-time password verification."""

    def test_verify_password_constant_time_with_valid_hash(self):
        """Test constant-time verification with a valid hash."""
        password = "test_password"
        hashed = hash_password(password)
        
        assert verify_password_constant_time(password, hashed) is True

    def test_verify_password_constant_time_with_wrong_password(self):
        """Test constant-time verification with wrong password."""
        password = "correct_password"
        wrong_password = "wrong_password"
        hashed = hash_password(password)
        
        assert verify_password_constant_time(wrong_password, hashed) is False

    def test_verify_password_constant_time_with_none_hash(self):
        """Test constant-time verification with None hash (non-existent user)."""
        password = "any_password"
        
        # Should always return False when hash is None
        assert verify_password_constant_time(password, None) is False

    def test_constant_time_behavior_similar_timing(self):
        """
        Test that verification takes similar time for non-existent user vs wrong password.
        
        This is a basic timing test to ensure bcrypt is being called in both cases.
        The timing should be in the same order of magnitude (both running bcrypt).
        """
        password = "test_password"
        hashed = hash_password("correct_password")
        
        # Time verification with wrong password (user exists)
        start = time.perf_counter()
        verify_password_constant_time(password, hashed)
        time_with_hash = time.perf_counter() - start
        
        # Time verification with None hash (user doesn't exist)
        start = time.perf_counter()
        verify_password_constant_time(password, None)
        time_with_none = time.perf_counter() - start
        
        # Both should take significant time (bcrypt is slow)
        # Typical bcrypt takes 100-300ms with 12 rounds
        assert time_with_hash > 0.05  # At least 50ms
        assert time_with_none > 0.05  # At least 50ms
        
        # The ratio should be within reasonable bounds (not 10x different)
        # Allow up to 3x variance due to system load
        ratio = max(time_with_hash, time_with_none) / min(time_with_hash, time_with_none)
        assert ratio < 3.0, f"Timing difference too large: {time_with_hash:.3f}s vs {time_with_none:.3f}s"


class TestJWTOperations:
    """Test JWT token creation and decoding."""

    def test_create_and_decode_access_token(self):
        """Test that we can create and decode access tokens."""
        payload = {"sub": "user123", "user_type": "admin"}
        token = create_access_token(payload)
        
        # Token should be a non-empty string
        assert isinstance(token, str)
        assert len(token) > 0
        
        # Decode should return the payload with additional fields
        decoded = decode_access_token(token)
        assert decoded is not None
        assert decoded["sub"] == "user123"
        assert decoded["user_type"] == "admin"
        assert "exp" in decoded
        assert "iat" in decoded
        assert "jti" in decoded

    def test_decode_invalid_token(self):
        """Test that invalid tokens return None."""
        invalid_token = "invalid.token.here"
        decoded = decode_access_token(invalid_token)
        
        assert decoded is None

    def test_decode_tampered_token(self):
        """Test that tampered tokens return None."""
        payload = {"sub": "user123"}
        token = create_access_token(payload)
        
        # Tamper with the token
        tampered = token[:-5] + "XXXXX"
        decoded = decode_access_token(tampered)
        
        assert decoded is None
