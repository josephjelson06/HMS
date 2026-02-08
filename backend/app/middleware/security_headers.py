from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add baseline security headers to all responses.

    Notes:
    - We intentionally do *not* set CSP here because `/docs` (Swagger UI) relies on
      inline scripts/styles and external assets by default.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)

        # Prevent MIME sniffing.
        response.headers.setdefault("X-Content-Type-Options", "nosniff")

        # Reduce cross-origin embedding risk for non-CORS resource types.
        # `same-origin` is the strictest and is broadly supported by tooling.
        response.headers.setdefault("Cross-Origin-Resource-Policy", "same-origin")

        # Basic clickjacking protection for HTML endpoints such as `/docs`.
        response.headers.setdefault("X-Frame-Options", "DENY")

        # Reduce referrer leakage.
        response.headers.setdefault("Referrer-Policy", "no-referrer")

        # Disable sensitive browser features by default.
        response.headers.setdefault(
            "Permissions-Policy",
            "geolocation=(), microphone=(), camera=()",
        )

        return response
