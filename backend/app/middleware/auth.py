from uuid import UUID

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.core.security import decode_access_token
from app.modules.audit.context import (
    AuditRuntimeContext,
    clear_audit_runtime_context,
    set_audit_runtime_context,
)


def extract_token(request: Request) -> str | None:
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.lower().startswith("bearer "):
        return auth_header.split(" ", 1)[1].strip()

    return request.cookies.get("access_token")


class JwtPayloadMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        token = extract_token(request)
        token_payload = decode_access_token(token) if token else None
        request.state.token_payload = token_payload
        
        # Set up audit runtime context for this request
        # Extract values from token_payload for audit logging
        tenant_id = None
        actor_user_id = None
        acting_as_user_id = None
        
        if token_payload:
            # Get tenant_id from token
            tenant_id_str = token_payload.get("tenant_id")
            if tenant_id_str:
                try:
                    tenant_id = UUID(tenant_id_str)
                except (ValueError, TypeError):
                    pass
            
            # Get user_id as actor_user_id
            user_id_str = token_payload.get("user_id")
            if user_id_str:
                try:
                    actor_user_id = UUID(user_id_str)
                except (ValueError, TypeError):
                    pass
            
            # Get impersonation info if present
            impersonation = token_payload.get("impersonation")
            if impersonation and isinstance(impersonation, dict):
                impersonated_by_str = impersonation.get("impersonated_by")
                if impersonated_by_str:
                    try:
                        # When impersonating, the actual admin is stored in acting_as_user_id
                        acting_as_user_id = UUID(impersonated_by_str)
                    except (ValueError, TypeError):
                        pass
        
        # Session will be None here - it gets passed explicitly to audit_event_stub
        # or set later in the route handler
        audit_ctx = AuditRuntimeContext(
            session=None,  # Session managed separately
            tenant_id=tenant_id,
            actor_user_id=actor_user_id,
            acting_as_user_id=acting_as_user_id,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )
        set_audit_runtime_context(audit_ctx)
        
        try:
            response = await call_next(request)
            return response
        finally:
            clear_audit_runtime_context()
