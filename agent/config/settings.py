from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # OpenAI Configuration
    openai_api_key: str
    openai_api_base: str

    # LLM Defaults
    default_model: str = "gpt-4.1-nano"
    default_temperature: float = 0.0

    # Memory Configuration
    memory_database_uri: Optional[str] = None
    memory_token_limit: int = 40000

    # Database Pool Configuration
    db_pool_size: int = 10
    db_max_overflow: int = 20
    db_pool_recycle: int = 3600  # seconds

    # Perplexity Configuration
    perplexity_api_key: Optional[str] = None
    perplexity_api_base_url: str = "https://api.perplexity.ai"
    perplexity_model: str = "sonar"

    # Observability (Arize Phoenix)
    phoenix_enabled: bool = True
    phoenix_endpoint: Optional[str] = None  # e.g., "http://localhost:6006"
    phoenix_project_name: str = "llamaindex-agents"  # Project name in Phoenix UI
    phoenix_batch_processor: bool = False  # True for production (async batched exports)


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance (singleton pattern)."""
    return Settings()
