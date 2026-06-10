from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://ase_app:ase_dev_password@postgres:5432/ase"
    REDIS_URL: str = "redis://redis:6379/0"
    LOG_LEVEL: str = "INFO"
    ENVIRONMENT: str = "development"

    # AI
    DEEPSEEK_API_KEY: str = ""
    OPENAI_API_KEY: str = ""

    # Scraping
    APIFY_API_KEY: str = ""
    BRIGHTDATA_USERNAME: str = ""
    BRIGHTDATA_PASSWORD: str = ""

    class Config:
        env_file = ".env"


settings = Settings()
