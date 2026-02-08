from uuid import UUID

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.core.security import decode_access_token
from app.modules.audit.context import (
    AuditRuntimeContext,
    clear_audit_runtime_context,
    set_audit_runtime_context,
)
from app.modules.auth.tokens import AccessTokenClaims, AccessTokenError, decode_access_token as decode_token_strict
from app.modules.tenant.context import resolve_auth_context_from_claims


def extract_token(request: Request) -> str | None:
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.lower().startswith("bearer "):
        return auth_header.split(" ", 1)[1].strip()

    return request.cookies.get("access_token")


def _to_uuid(value: object) -> UUID | None:
    if value is None:
        return None
    try:
        return UUID(str(value))
    except (ValueError, TypeError):
        return None


class JwtPayloadMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        token = extract_token(request)
        token_payload = decode_access_token(token) if token else None
        request.state.token_payload = token_payload

        # Store typed claims for strict auth dependencies.
        try:
            request.state.token_claims = decode_token_strict(token) if token else None
        except AccessTokenError:
            request.state.token_claims = None

        # Also provide lightweight auth context from claims (no DB lookup).
        request.state.auth_context = resolve_auth_context_from_claims(token_payload)

        # Populate request-scoped audit context from JWT claims.
        tenant_id = _to_uuid(token_payload.get("tenant_id")) if isinstance(token_payload, dict) else None
        actor_user_id = _to_uuid(token_payload.get("sub")) if isinstance(token_payload, dict) else None
        acting_as_user_id = None

        if isinstance(token_payload, dict):
            impersonation = token_payload.get("impersonation")
            if isinstance(impersonation, dict):
                impersonation_actor = _to_uuid(impersonation.get("actor_user_id"))
                acting_as_user_id = _to_uuid(impersonation.get("acting_as_user_id"))
                if impersonation_actor is not None:
                    actor_user_id = impersonation_actor

        audit_ctx = AuditRuntimeContext(
            session=None,
            tenant_id=tenant_id,
            actor_user_id=actor_user_id,
            acting_as_user_id=acting_as_user_id,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )
        set_audit_runtime_context(audit_ctx)

        try:
            return await call_next(request)
        finally:
            clear_audit_runtime_context()
