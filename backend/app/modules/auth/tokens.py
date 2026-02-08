from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import jwt
from jwt import InvalidTokenError
from starlette.responses import Response

from app.core.config import settings


JWT_ALGORITHM = "HS256"


class AccessTokenError(ValueError):
    """Raised when an access token is invalid, expired, or malformed."""
    pass


@dataclass(frozen=True)
class AccessTokenClaims:
    """Immutable, typed representation of JWT access token claims."""
    user_id: UUID
    user_type: str
    roles: tuple[str, ...]
    jti: UUID
    issued_at: datetime
    expires_at: datetime
    tenant_id: UUID | None = None
    actor_user_id: UUID | None = None
    acting_as_user_id: UUID | None = None

    @property
    def effective_user_id(self) -> UUID:
        """Returns the acting_as_user_id if impersonating, otherwise user_id."""
        return self.acting_as_user_id or self.user_id


def create_access_token(
    *,
    user_id: UUID,
    user_type: str,
    roles: list[str],
    tenant_id: UUID | None = None,
    actor_user_id: UUID | None = None,
    acting_as_user_id: UUID | None = None,
    expires_delta: timedelta | None = None,
) -> tuple[str, AccessTokenClaims]:
    """Create a JWT access token and return both the encoded string and typed claims.
    
    This replaces the old create_access_token() which returned only the encoded string.
    """
    issued_at = datetime.now(UTC)
    expires_at = issued_at + (expires_delta or timedelta(minutes=settings.jwt_access_ttl_minutes))
    jti = uuid4()

    payload: dict[str, object] = {
        "sub": str(user_id),
        "user_type": user_type,
        "roles": roles,
        "jti": str(jti),
        "iat": int(issued_at.timestamp()),
        "exp": int(expires_at.timestamp()),
    }

    if tenant_id is not None:
        payload["tenant_id"] = str(tenant_id)

    if actor_user_id is not None or acting_as_user_id is not None:
        payload["impersonation"] = {
            "actor_user_id": str(actor_user_id) if actor_user_id is not None else None,
            "acting_as_user_id": str(acting_as_user_id) if acting_as_user_id is not None else None,
        }

    encoded = jwt.encode(payload, settings.jwt_secret, algorithm=JWT_ALGORITHM)

    claims = AccessTokenClaims(
        user_id=user_id,
        user_type=user_type,
        roles=tuple(roles),
        jti=jti,
        issued_at=issued_at,
        expires_at=expires_at,
        tenant_id=tenant_id,
        actor_user_id=actor_user_id,
        acting_as_user_id=acting_as_user_id,
    )
    return encoded, claims


def decode_access_token(token: str) -> AccessTokenClaims:
    """Decode and strictly validate a JWT access token.
    
    Unlike the old decode_access_token() which returned dict|None,
    this raises AccessTokenError on any problem - no silent failures.
    """
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[JWT_ALGORITHM],
            options={"require": ["sub", "user_type", "roles", "jti", "iat", "exp"]},
        )
    except InvalidTokenError as exc:
        raise AccessTokenError("Invalid or expired access token.") from exc

    try:
        user_id = UUID(str(payload["sub"]))
        user_type = str(payload["user_type"])
        roles_raw = payload["roles"]
        if not isinstance(roles_raw, list) or not all(isinstance(r, str) for r in roles_raw):
            raise ValueError("roles must be a list of strings.")
        jti = UUID(str(payload["jti"]))
        issued_at = datetime.fromtimestamp(int(payload["iat"]), UTC)
        expires_at = datetime.fromtimestamp(int(payload["exp"]), UTC)
    except (KeyError, ValueError, TypeError) as exc:
        raise AccessTokenError("Access token payload is malformed.") from exc

    tenant_id = None
    tenant_id_raw = payload.get("tenant_id")
    if tenant_id_raw is not None:
        try:
            tenant_id = UUID(str(tenant_id_raw))
        except (ValueError, TypeError) as exc:
            raise AccessTokenError("Access token tenant_id is malformed.") from exc

    actor_user_id = None
    acting_as_user_id = None
    impersonation = payload.get("impersonation")
    if impersonation is not None:
        if not isinstance(impersonation, dict):
            raise AccessTokenError("Access token impersonation payload is malformed.")
        actor_raw = impersonation.get("actor_user_id")
        acting_raw = impersonation.get("acting_as_user_id")
        try:
            actor_user_id = UUID(actor_raw) if actor_raw else None
            acting_as_user_id = UUID(acting_raw) if acting_raw else None
        except (ValueError, TypeError) as exc:
            raise AccessTokenError("Access token impersonation IDs are malformed.") from exc

    return AccessTokenClaims(
        user_id=user_id,
        user_type=user_type,
        roles=tuple(roles_raw),
        jti=jti,
        issued_at=issued_at,
        expires_at=expires_at,
        tenant_id=tenant_id,
        actor_user_id=actor_user_id,
        acting_as_user_id=acting_as_user_id,
    )


def set_access_token_cookie(response: Response, *, token: str) -> None:
    """Set the access token as an HttpOnly cookie with appropriate settings."""
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
        max_age=settings.jwt_access_ttl_minutes * 60,
        path="/",
        domain=settings.cookie_domain,
    )


def set_refresh_token_cookie(response: Response, *, token: str) -> None:
    """Set the refresh token as an HttpOnly cookie with appropriate settings."""
    response.set_cookie(
        key="refresh_token",
        value=token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
        max_age=settings.jwt_refresh_ttl_days * 24 * 60 * 60,
        path="/",
        domain=settings.cookie_domain,
    )


def set_csrf_token_cookie(response: Response, *, token: str) -> None:
    """Set the CSRF token as a JS-readable cookie."""
    response.set_cookie(
        key="csrf_token",
        value=token,
        httponly=False,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
        max_age=settings.jwt_refresh_ttl_days * 24 * 60 * 60,
        path="/",
        domain=settings.cookie_domain,
    )


def clear_auth_cookies(response: Response) -> None:
    """Clear all auth-related cookies."""
    response.delete_cookie("access_token", path="/", domain=settings.cookie_domain)
    response.delete_cookie("refresh_token", path="/", domain=settings.cookie_domain)
    response.delete_cookie("csrf_token", path="/", domain=settings.cookie_domain)

