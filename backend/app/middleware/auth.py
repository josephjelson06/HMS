from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.core.security import decode_access_token
from app.modules.auth.tokens import AccessTokenClaims, AccessTokenError, decode_access_token as decode_token_strict
from app.modules.tenant.context import resolve_auth_context_from_claims


def extract_token(request: Request) -> str | None:
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.lower().startswith("bearer "):
        return auth_header.split(" ", 1)[1].strip()

    return request.cookies.get("access_token")


class JwtPayloadMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        token = extract_token(request)
        request.state.token_payload = decode_access_token(token) if token else None

        # Store typed claims for strict auth dependencies.
        try:
            request.state.token_claims = decode_token_strict(token) if token else None
        except AccessTokenError:
            request.state.token_claims = None

        # Also provide lightweight auth context from claims (no DB lookup).
        request.state.auth_context = resolve_auth_context_from_claims(
            getattr(request.state, "token_payload", None)
        )

        return await call_next(request)
