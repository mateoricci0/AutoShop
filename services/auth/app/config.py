"""Auth service configuration via Pydantic Settings."""

from __future__ import annotations

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://ase_app:password@postgres:5432/ase"
    REDIS_URL: str = "redis://redis:6379/0"
    FERNET_KEY: str = ""
    ADMIN_PASSWORD_HASH: str = ""  # bcrypt hash of the admin password
    SESSION_TTL_SECONDS: int = 2592000  # 30 days
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"
    SERVICE_NAME: str = "auth"

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
