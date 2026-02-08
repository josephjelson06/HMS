from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.modules.tenant.context import resolve_auth_context_from_claims


class TenantContextMiddleware(BaseHTTPMiddleware):
    """Middleware that resolves AuthContext from JWT claims and stores it in request.state.
    
    This runs AFTER the JWT middleware (which sets request.state.token_payload)
    and BEFORE route handlers.
    
    It constructs an immutable AuthContext and attaches it to request.state.auth_context.
    Future enhancement: can also SET LOCAL app.tenant_id in PostgreSQL for RLS.
    """

    async def dispatch(self, request: Request, call_next):
        # Read token payload set by JwtPayloadMiddleware
        claims = getattr(request.state, "token_payload", None)

        # Resolve auth context from claims (no DB hit)
        auth_context = resolve_auth_context_from_claims(claims)
        request.state.auth_context = auth_context

        response = await call_next(request)
        return response
