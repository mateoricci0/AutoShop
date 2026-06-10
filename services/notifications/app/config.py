from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://ase_app:ase_dev_password@postgres:5432/ase"
    REDIS_URL: str = "redis://redis:6379/0"
    LOG_LEVEL: str = "INFO"
    ENVIRONMENT: str = "development"

    # Email
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASS: str = ""

    # Channels
    DISCORD_WEBHOOK: str = ""
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_CHAT_ID: str = ""
    SLACK_WEBHOOK: str = ""

    class Config:
        env_file = ".env"


settings = Settings()
