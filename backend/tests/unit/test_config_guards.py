"""Tests for startup configuration guards."""
import os
from unittest import mock

import pytest
from pydantic import ValidationError

from app.core.config import Settings


def test_strong_jwt_secret_passes():
    """App starts successfully with a strong JWT_SECRET (32+ chars)."""
    with mock.patch.dict(
        os.environ,
        {
            "DATABASE_URL": "postgresql+asyncpg://test:test@localhost/test",
            "JWT_SECRET": "this-is-a-very-strong-secret-with-more-than-32-characters",
        },
    ):
        settings = Settings()
        # Should not raise
        settings.validate_startup_guards()


def test_weak_jwt_secret_fails():
    """App refuses to start with JWT_SECRET='secret'."""
    with mock.patch.dict(
        os.environ,
        {
            "DATABASE_URL": "postgresql+asyncpg://test:test@localhost/test",
            "JWT_SECRET": "secret",
        },
    ):
        settings = Settings()
        with pytest.raises(ValueError, match="JWT_SECRET is weak"):
            settings.validate_startup_guards()


def test_empty_jwt_secret_fails():
    """App refuses to start with JWT_SECRET=''."""
    with mock.patch.dict(
        os.environ,
        {
            "DATABASE_URL": "postgresql+asyncpg://test:test@localhost/test",
            "JWT_SECRET": "",
        },
    ):
        settings = Settings()
        with pytest.raises(ValueError, match="JWT_SECRET is weak"):
            settings.validate_startup_guards()


def test_short_jwt_secret_fails():
    """App refuses to start with JWT_SECRET less than 32 chars."""
    with mock.patch.dict(
        os.environ,
        {
            "DATABASE_URL": "postgresql+asyncpg://test:test@localhost/test",
            "JWT_SECRET": "short-secret",
        },
    ):
        settings = Settings()
        with pytest.raises(ValueError, match="JWT_SECRET is weak"):
            settings.validate_startup_guards()


def test_known_weak_jwt_secret_fails():
    """App refuses to start with known weak secrets."""
    weak_secrets = ["changeme", "change-me", "default", "password", "dev-secret"]
    for weak_secret in weak_secrets:
        # Pad to meet 32 char requirement but still in weak list
        padded_secret = weak_secret
        with mock.patch.dict(
            os.environ,
            {
                "DATABASE_URL": "postgresql+asyncpg://test:test@localhost/test",
                "JWT_SECRET": padded_secret,
            },
        ):
            settings = Settings()
            with pytest.raises(ValueError, match="JWT_SECRET is weak"):
                settings.validate_startup_guards()


def test_development_with_insecure_cookie_passes():
    """App starts in development mode with COOKIE_SECURE=false."""
    with mock.patch.dict(
        os.environ,
        {
            "DATABASE_URL": "postgresql+asyncpg://test:test@localhost/test",
            "JWT_SECRET": "this-is-a-very-strong-secret-with-more-than-32-characters",
            "ENVIRONMENT": "development",
            "COOKIE_SECURE": "false",
        },
    ):
        settings = Settings()
        # Should not raise
        settings.validate_startup_guards()


def test_production_with_insecure_cookie_fails():
    """App refuses to start in production mode with COOKIE_SECURE=false."""
    with mock.patch.dict(
        os.environ,
        {
            "DATABASE_URL": "postgresql+asyncpg://test:test@localhost/test",
            "JWT_SECRET": "this-is-a-very-strong-secret-with-more-than-32-characters",
            "ENVIRONMENT": "production",
            "COOKIE_SECURE": "false",
        },
    ):
        settings = Settings()
        with pytest.raises(ValueError, match="COOKIE_SECURE must be true in production"):
            settings.validate_startup_guards()


def test_production_with_seed_data_fails():
    """App refuses to start in production mode with SEED_DATA=true."""
    with mock.patch.dict(
        os.environ,
        {
            "DATABASE_URL": "postgresql+asyncpg://test:test@localhost/test",
            "JWT_SECRET": "this-is-a-very-strong-secret-with-more-than-32-characters",
            "ENVIRONMENT": "production",
            "COOKIE_SECURE": "true",
            "SEED_DATA": "true",
            "CORS_ORIGINS": "https://example.com",
        },
    ):
        settings = Settings()
        with pytest.raises(ValueError, match="SEED_DATA must be false in production"):
            settings.validate_startup_guards()


def test_jwt_access_ttl_too_low_fails():
    """App refuses to start with JWT_ACCESS_TTL_MINUTES=0."""
    with mock.patch.dict(
        os.environ,
        {
            "DATABASE_URL": "postgresql+asyncpg://test:test@localhost/test",
            "JWT_SECRET": "this-is-a-very-strong-secret-with-more-than-32-characters",
            "JWT_ACCESS_TTL_MINUTES": "0",
        },
    ):
        settings = Settings()
        with pytest.raises(ValueError, match="JWT_ACCESS_TTL_MINUTES must be between 5 and 30"):
            settings.validate_startup_guards()


def test_jwt_access_ttl_too_high_fails():
    """App refuses to start with JWT_ACCESS_TTL_MINUTES=60."""
    with mock.patch.dict(
        os.environ,
        {
            "DATABASE_URL": "postgresql+asyncpg://test:test@localhost/test",
            "JWT_SECRET": "this-is-a-very-strong-secret-with-more-than-32-characters",
            "JWT_ACCESS_TTL_MINUTES": "60",
        },
    ):
        settings = Settings()
        with pytest.raises(ValueError, match="JWT_ACCESS_TTL_MINUTES must be between 5 and 30"):
            settings.validate_startup_guards()


def test_jwt_access_ttl_10_passes():
    """App starts with JWT_ACCESS_TTL_MINUTES=10."""
    with mock.patch.dict(
        os.environ,
        {
            "DATABASE_URL": "postgresql+asyncpg://test:test@localhost/test",
            "JWT_SECRET": "this-is-a-very-strong-secret-with-more-than-32-characters",
            "JWT_ACCESS_TTL_MINUTES": "10",
        },
    ):
        settings = Settings()
        # Should not raise
        settings.validate_startup_guards()


def test_jwt_access_ttl_15_passes():
    """App starts with JWT_ACCESS_TTL_MINUTES=15 (backward compat)."""
    with mock.patch.dict(
        os.environ,
        {
            "DATABASE_URL": "postgresql+asyncpg://test:test@localhost/test",
            "JWT_SECRET": "this-is-a-very-strong-secret-with-more-than-32-characters",
            "JWT_ACCESS_TTL_MINUTES": "15",
        },
    ):
        settings = Settings()
        # Should not raise
        settings.validate_startup_guards()


def test_jwt_refresh_ttl_zero_fails():
    """App refuses to start with JWT_REFRESH_TTL_DAYS=0."""
    with mock.patch.dict(
        os.environ,
        {
            "DATABASE_URL": "postgresql+asyncpg://test:test@localhost/test",
            "JWT_SECRET": "this-is-a-very-strong-secret-with-more-than-32-characters",
            "JWT_REFRESH_TTL_DAYS": "0",
        },
    ):
        settings = Settings()
        with pytest.raises(ValueError, match="JWT_REFRESH_TTL_DAYS must be greater than 0"):
            settings.validate_startup_guards()


def test_jwt_refresh_ttl_negative_fails():
    """App refuses to start with negative JWT_REFRESH_TTL_DAYS."""
    with mock.patch.dict(
        os.environ,
        {
            "DATABASE_URL": "postgresql+asyncpg://test:test@localhost/test",
            "JWT_SECRET": "this-is-a-very-strong-secret-with-more-than-32-characters",
            "JWT_REFRESH_TTL_DAYS": "-1",
        },
    ):
        settings = Settings()
        with pytest.raises(ValueError, match="JWT_REFRESH_TTL_DAYS must be greater than 0"):
            settings.validate_startup_guards()


def test_samesite_none_without_secure_fails():
    """App refuses to start with COOKIE_SAMESITE=none and COOKIE_SECURE=false."""
    with mock.patch.dict(
        os.environ,
        {
            "DATABASE_URL": "postgresql+asyncpg://test:test@localhost/test",
            "JWT_SECRET": "this-is-a-very-strong-secret-with-more-than-32-characters",
            "COOKIE_SAMESITE": "none",
            "COOKIE_SECURE": "false",
        },
    ):
        settings = Settings()
        with pytest.raises(ValueError, match="COOKIE_SAMESITE=none requires COOKIE_SECURE=true"):
            settings.validate_startup_guards()


def test_samesite_none_with_secure_passes():
    """App starts with COOKIE_SAMESITE=none and COOKIE_SECURE=true."""
    with mock.patch.dict(
        os.environ,
        {
            "DATABASE_URL": "postgresql+asyncpg://test:test@localhost/test",
            "JWT_SECRET": "this-is-a-very-strong-secret-with-more-than-32-characters",
            "COOKIE_SAMESITE": "none",
            "COOKIE_SECURE": "true",
        },
    ):
        settings = Settings()
        # Should not raise
        settings.validate_startup_guards()


def test_production_cors_wildcard_fails():
    """App refuses to start in production with CORS_ORIGINS containing '*'."""
    with mock.patch.dict(
        os.environ,
        {
            "DATABASE_URL": "postgresql+asyncpg://test:test@localhost/test",
            "JWT_SECRET": "this-is-a-very-strong-secret-with-more-than-32-characters",
            "ENVIRONMENT": "production",
            "COOKIE_SECURE": "true",
            "SEED_DATA": "false",
            "CORS_ORIGINS": "https://example.com,*",
        },
    ):
        settings = Settings()
        with pytest.raises(ValueError, match="CORS_ORIGINS must not contain wildcard origins in production"):
            settings.validate_startup_guards()


def test_production_cors_http_fails():
    """App refuses to start in production with CORS_ORIGINS containing 'http://...'."""
    with mock.patch.dict(
        os.environ,
        {
            "DATABASE_URL": "postgresql+asyncpg://test:test@localhost/test",
            "JWT_SECRET": "this-is-a-very-strong-secret-with-more-than-32-characters",
            "ENVIRONMENT": "production",
            "COOKIE_SECURE": "true",
            "SEED_DATA": "false",
            "CORS_ORIGINS": "http://example.com",
        },
    ):
        settings = Settings()
        with pytest.raises(ValueError, match="Production CORS_ORIGINS must use https"):
            settings.validate_startup_guards()


def test_production_with_valid_settings_passes():
    """App starts in production with all valid settings."""
    with mock.patch.dict(
        os.environ,
        {
            "DATABASE_URL": "postgresql+asyncpg://test:test@localhost/test",
            "JWT_SECRET": "this-is-a-very-strong-secret-with-more-than-32-characters",
            "ENVIRONMENT": "production",
            "COOKIE_SECURE": "true",
            "SEED_DATA": "false",
            "CORS_ORIGINS": "https://example.com,https://app.example.com",
            "JWT_ACCESS_TTL_MINUTES": "10",
        },
    ):
        settings = Settings()
        # Should not raise
        settings.validate_startup_guards()


def test_default_jwt_access_ttl_is_10():
    """Verify default JWT_ACCESS_TTL_MINUTES is lowered to 10."""
    with mock.patch.dict(
        os.environ,
        {
            "DATABASE_URL": "postgresql+asyncpg://test:test@localhost/test",
            "JWT_SECRET": "this-is-a-very-strong-secret-with-more-than-32-characters",
        },
    ):
        settings = Settings()
        assert settings.jwt_access_ttl_minutes == 10
