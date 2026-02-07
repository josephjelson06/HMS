from datetime import datetime, timedelta, timezone
import hashlib
import secrets
import uuid

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def verify_password_constant_time(plain_password: str, hashed_password: str | None) -> bool:
    """Verify password in constant time to prevent timing attacks.
    
    Returns False if hashed_password is None without short-circuiting.
    """
    if hashed_password is None:
        # Still hash to maintain constant time
        pwd_context.hash(plain_password)
        return False
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    expire = now + (expires_delta or timedelta(minutes=settings.jwt_access_ttl_minutes))
    to_encode.update({"exp": expire, "iat": now, "jti": str(uuid.uuid4())})
    return jwt.encode(to_encode, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except JWTError:
        return None


def create_refresh_token() -> tuple[str, str]:
    token = secrets.token_urlsafe(48)
    jti = str(uuid.uuid4())
    return token, jti


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def generate_csrf_token() -> str:
    return secrets.token_urlsafe(32)
