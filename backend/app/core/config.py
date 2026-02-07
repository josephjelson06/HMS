import json
from typing import Annotated
from urllib.parse import urlparse

from pydantic import field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


KNOWN_WEAK_SECRETS = {
    "",
    "changeme",
    "change-me",
    "default",
    "jwt-secret",
    "secret",
    "password",
    "dev-secret",
    "replace-with-at-least-32-random-characters",
}


class Settings(BaseSettings):
    app_name: str = "HMS"
    environment: str = "development"
    database_url: str
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    jwt_access_ttl_minutes: int = 10
    jwt_refresh_ttl_days: int = 7
    cookie_secure: bool = False
    cookie_domain: str | None = None
    cookie_samesite: str = "lax"
    cors_origins: Annotated[list[str], NoDecode] = ["http://localhost:3000"]
    seed_data: bool = True
    reports_storage_path: str = "storage/reports"
    report_export_poll_seconds: int = 3
    report_export_batch_size: int = 5

    admin_seed_email: str = "admin@demo.com"
    admin_seed_password: str = "Admin123!"
    hotel_seed_email: str = "manager@demo.com"
    hotel_seed_password: str = "Manager123!"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value):
        if isinstance(value, str):
            raw = value.strip()
            if not raw:
                return []
            if raw.startswith("["):
                parsed = json.loads(raw)
                if not isinstance(parsed, list):
                    raise ValueError("CORS_ORIGINS JSON value must be a list")
                return [str(item).strip() for item in parsed if str(item).strip()]
            return [item.strip() for item in raw.split(",") if item.strip()]
        return value

    def validate_startup_guards(self) -> None:
        """Validate security-critical configuration at startup."""
        # 1. JWT secret strength
        normalized_secret = self.jwt_secret.strip().lower()
        if len(self.jwt_secret.strip()) < 32 or normalized_secret in KNOWN_WEAK_SECRETS:
            raise ValueError(
                "JWT_SECRET is weak. Use a high-entropy secret of at least 32 characters."
            )

        # 2. Production cookie security
        if self.environment == "production" and not self.cookie_secure:
            raise ValueError("COOKIE_SECURE must be true in production.")

        # 3. No seed data in production
        if self.environment == "production" and self.seed_data:
            raise ValueError("SEED_DATA must be false in production.")

        # 4. Access token TTL bounds
        if not 5 <= self.jwt_access_ttl_minutes <= 30:
            raise ValueError(
                "JWT_ACCESS_TTL_MINUTES must be between 5 and 30."
            )

        # 5. Refresh token TTL must be positive
        if self.jwt_refresh_ttl_days <= 0:
            raise ValueError("JWT_REFRESH_TTL_DAYS must be greater than 0.")

        # 6. SameSite=none requires Secure=true
        if self.cookie_samesite.lower() == "none" and not self.cookie_secure:
            raise ValueError(
                "COOKIE_SAMESITE=none requires COOKIE_SECURE=true."
            )

        # 7. CORS origins must not contain wildcards in production
        if self.environment == "production":
            for origin in self.cors_origins:
                if "*" in origin:
                    raise ValueError(
                        "CORS_ORIGINS must not contain wildcard origins in production."
                    )
                parsed = urlparse(origin)
                if parsed.scheme != "https":
                    raise ValueError(
                        f"Production CORS_ORIGINS must use https: {origin}"
                    )


settings = Settings()
