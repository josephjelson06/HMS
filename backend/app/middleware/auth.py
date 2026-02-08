from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.core.security import decode_access_token
from app.modules.auth.tokens import AccessTokenClaims, AccessTokenError, decode_access_token as decode_token_strict


def extract_token(request: Request) -> str | None:
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.lower().startswith("bearer "):
        return auth_header.split(" ", 1)[1].strip()

    return request.cookies.get("access_token")


class JwtPayloadMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        token = extract_token(request)
        request.state.token_payload = decode_access_token(token) if token else None
        
        # Also store typed claims for the new dependency
        try:
            request.state.token_claims = decode_token_strict(token) if token else None
        except AccessTokenError:
            request.state.token_claims = None
        
        return await call_next(request)
