import hmac
import secrets
from urllib.parse import urlparse

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.core.config import settings

SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}
EXEMPT_PATHS = {"/api/auth/login", "/api/auth/refresh"}
CSRF_TOKEN_BYTES = 32
CSRF_COOKIE_NAME = "csrf_token"
CSRF_HEADER_NAME = "X-CSRF-Token"


class CSRFValidationError(Exception):
    def __init__(self, detail: str, status_code: int = 403):
        super().__init__(detail)
        self.detail = detail
        self.status_code = status_code


class CsrfMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.method not in SAFE_METHODS:
            try:
                self._validate_origin_or_referer(request)
                if request.url.path not in EXEMPT_PATHS:
                    self._validate_double_submit_token(request)
            except CSRFValidationError as exc:
                response = JSONResponse(
                    status_code=exc.status_code,
                    content={"detail": exc.detail},
                )
                self._ensure_csrf_cookie(request, response)
                return response

        response = await call_next(request)
        self._ensure_csrf_cookie(request, response)
        return response

    def _validate_origin_or_referer(self, request: Request) -> None:
        """Validate that Origin or Referer header comes from an allowed origin."""
        origin = request.headers.get("origin")
        referer = request.headers.get("referer")

        # If neither header is present, skip origin check
        # (double-submit token check will still protect)
        if not origin and not referer:
            return

        allowed_origins = self._get_allowed_origins()

        if origin:
            normalized = origin.rstrip("/")
            if normalized in allowed_origins:
                return
            raise CSRFValidationError(f"Origin '{origin}' is not allowed.")

        if referer:
            parsed = urlparse(referer)
            referer_origin = f"{parsed.scheme}://{parsed.netloc}".rstrip("/")
            if referer_origin in allowed_origins:
                return
            raise CSRFValidationError(f"Referer origin '{referer_origin}' is not allowed.")

    def _validate_double_submit_token(self, request: Request) -> None:
        """Validate CSRF double-submit: cookie value must match header value (timing-safe)."""
        cookie_token = request.cookies.get(CSRF_COOKIE_NAME)
        header_token = request.headers.get(CSRF_HEADER_NAME)

        if not cookie_token or not header_token:
            raise CSRFValidationError("CSRF token missing or invalid")

        if not hmac.compare_digest(cookie_token, header_token):
            raise CSRFValidationError("CSRF token mismatch")

    def _ensure_csrf_cookie(self, request: Request, response: Response) -> None:
        """Auto-issue a CSRF cookie if one doesn't already exist."""
        existing_token = request.cookies.get(CSRF_COOKIE_NAME)
        if existing_token:
            return

        csrf_token = secrets.token_urlsafe(CSRF_TOKEN_BYTES)
        response.set_cookie(
            key=CSRF_COOKIE_NAME,
            value=csrf_token,
            httponly=False,  # JS must be able to read this to send as header
            secure=settings.cookie_secure,
            samesite=settings.cookie_samesite,
            max_age=settings.jwt_refresh_ttl_days * 24 * 60 * 60,
            path="/",
            domain=settings.cookie_domain,
        )

    def _get_allowed_origins(self) -> set[str]:
        """Build the set of allowed origins from CORS config."""
        return {origin.rstrip("/") for origin in settings.cors_origins}
