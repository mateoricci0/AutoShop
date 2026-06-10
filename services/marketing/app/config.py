from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://ase_app:ase_dev_password@postgres:5432/ase"
    REDIS_URL: str = "redis://redis:6379/0"
    LOG_LEVEL: str = "INFO"
    ENVIRONMENT: str = "development"

    # AI
    DEEPSEEK_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    LLM_PRIMARY: str = "deepseek"
    LLM_PREMIUM: str = "openai"

    class Config:
        env_file = ".env"


settings = Settings()
