from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.core.security import decode_access_token
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
        
        # Resolve auth context from typed claims
        request.state.auth_context = resolve_auth_context_from_claims(
            getattr(request.state, "token_payload", None)
        )
        
        return await call_next(request)
