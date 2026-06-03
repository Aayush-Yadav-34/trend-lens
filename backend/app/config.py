"""
Configuration module for Trend Lens backend.

Uses pydantic-settings to read all environment variables from .env file.
Every configurable value in the application flows through this Settings class —
no module should ever read os.environ directly.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables and .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # PostgreSQL
    DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost:5432/trendlens"

    # Redis
    REDIS_URL: str = "redis://localhost:6379"

    # Reddit API
    REDDIT_CLIENT_ID: str = ""
    REDDIT_CLIENT_SECRET: str = ""
    REDDIT_USER_AGENT: str = "TrendLens/1.0 by TrendLensBot"

    # Application
    ENVIRONMENT: str = "development"
    CORS_ORIGINS: str = "http://localhost:5173"
    CACHE_TTL_SECONDS: int = 900
    SCRAPE_INTERVAL_MINUTES: int = 30
    N_CLUSTERS: int = 8

    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS_ORIGINS comma-separated string into a list."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]


settings = Settings()
