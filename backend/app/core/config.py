import json
from typing import Annotated

from pydantic import field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "HMS"
    environment: str = "development"
    database_url: str
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    jwt_access_ttl_minutes: int = 15
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


settings = Settings()
