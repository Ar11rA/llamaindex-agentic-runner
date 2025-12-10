from enum import Enum
from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class LLMProvider(str, Enum):
    """Supported LLM providers."""

    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GEMINI_VERTEX = "gemini_vertex"
    BEDROCK = "bedrock"
    COHERE = "cohere"


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Default LLM Provider
    llm_provider: LLMProvider = LLMProvider.OPENAI

    # LLM Defaults
    default_model: str = "gpt-4.1-nano"
    default_temperature: float = 0.0

    # OpenAI Configuration
    openai_api_key: Optional[str] = None
    openai_api_base: str = "https://api.openai.com/v1"

    # Anthropic Configuration
    anthropic_api_key: Optional[str] = None
    anthropic_api_base: str = "https://api.anthropic.com"

    # Gemini Vertex AI Configuration (OAuth Token mode with custom base URL)
    gemini_vertex_base_url: Optional[str] = None  # e.g., "https://vertexai.example.com"
    gemini_vertex_access_token: Optional[str] = None
    gemini_vertex_project: str = "aigateway"
    gemini_vertex_location: str = "global"
    gemini_vertex_api_version: str = "v1"

    # AWS Bedrock Configuration (Bearer Token mode with custom endpoint)
    bedrock_endpoint_url: Optional[str] = (
        None  # e.g., "https://aws-bedrock.ai-gateway.com/..."
    )
    bedrock_bearer_token: Optional[str] = (
        None  # Or use AWS_BEARER_TOKEN_BEDROCK env var
    )
    bedrock_region: str = "us-east-1"
    bedrock_model_id: str = "us.anthropic.claude-3-5-haiku-20241022-v1:0"

    # Cohere Configuration
    cohere_api_key: Optional[str] = None
    cohere_api_base: Optional[str] = None  # Custom base URL (e.g., AI Gateway)
    cohere_model: str = "command-r-plus"

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
