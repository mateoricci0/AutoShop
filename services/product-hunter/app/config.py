from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Infrastructure
    DATABASE_URL: str = "postgresql+asyncpg://ase_app:ase_dev_password@postgres:5432/ase"
    REDIS_URL: str = "redis://redis:6379/0"
    LOG_LEVEL: str = "INFO"
    ENVIRONMENT: str = "development"
    SERVICE_NAME: str = "product-hunter"

    # AI — DeepSeek (OpenAI-compatible)
    DEEPSEEK_API_KEY: str = ""
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com"
    DEEPSEEK_MODEL: str = "deepseek-chat"
    OPENAI_API_KEY: str = ""
    LLM_PRIMARY: str = "deepseek"

    # Scraping — optional
    APIFY_API_KEY: str = ""
    REDDIT_CLIENT_ID: str = ""
    REDDIT_CLIENT_SECRET: str = ""
    REDDIT_USER_AGENT: str = "ASE Product Hunter 1.0"

    # Scoring thresholds
    AUTO_APPROVE_THRESHOLD: float = 75.0
    MIN_SUCCESS_SCORE: float = 30.0

    # Scraping limits
    SCRAPE_LIMIT_PER_SOURCE: int = 20
    PLAYWRIGHT_POOL_SIZE: int = 3
    PLAYWRIGHT_TIMEOUT_MS: int = 30000


settings = Settings()
