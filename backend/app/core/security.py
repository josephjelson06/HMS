from datetime import datetime, timedelta, timezone
import hashlib
import secrets
import uuid

import bcrypt
import jwt
from jwt import InvalidTokenError

from app.core.config import settings


# Dummy hash pre-computed at module load time for constant-time verification.
# Must use same cost factor (12 rounds) as real hashes to ensure timing consistency.
# Used when verifying passwords for non-existent users to prevent timing attacks.
DUMMY_HASH = bcrypt.hashpw(b"dummy-password-never-used", bcrypt.gensalt(rounds=12))


def hash_password(password: str) -> str:
    """Hash a password using bcrypt with 12 rounds."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    """
    Verify a password against a hash using constant-time comparison.
    
    Uses bcrypt.checkpw for verification, which internally does constant-time
    comparison to prevent timing attacks at the hash comparison level.
    """
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except (ValueError, TypeError):
        # Invalid hash format
        return False


def verify_password_constant_time(password: str, password_hash: str | None) -> bool:
    """
    Verify a password in constant time, preventing user enumeration.
    
    When password_hash is None (user doesn't exist), still runs bcrypt
    against a dummy hash to match the timing of a real verification.
    This prevents attackers from distinguishing between "user exists"
    and "user doesn't exist" based on response time.
    """
    if password_hash is None:
        # User doesn't exist - compute against dummy to match timing
        # Explicitly discard result as we only care about timing
        _ = bcrypt.hashpw(password.encode("utf-8"), DUMMY_HASH)
        return False
    return verify_password(password, password_hash)


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    # DEPRECATED: Use app.modules.auth.tokens.create_access_token / decode_access_token instead.
    # Kept temporarily for backward compatibility during migration.
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    expire = now + (expires_delta or timedelta(minutes=settings.jwt_access_ttl_minutes))
    to_encode.update({"exp": expire, "iat": now, "jti": str(uuid.uuid4())})
    return jwt.encode(to_encode, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict | None:
    # DEPRECATED: Use app.modules.auth.tokens.create_access_token / decode_access_token instead.
    # Kept temporarily for backward compatibility during migration.
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except InvalidTokenError:
        return None


def create_refresh_token() -> tuple[str, str]:
    token = secrets.token_urlsafe(48)
    jti = str(uuid.uuid4())
    return token, jti


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def generate_csrf_token() -> str:
    return secrets.token_urlsafe(32)
