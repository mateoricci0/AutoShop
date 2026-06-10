from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://ase_app:ase_dev_password@postgres:5432/ase"
    REDIS_URL: str = "redis://redis:6379/0"
    LOG_LEVEL: str = "INFO"
    ENVIRONMENT: str = "development"

    FERNET_KEY: str = ""
    SHOPIFY_API_VERSION: str = "2024-10"

    class Config:
        env_file = ".env"


settings = Settings()
