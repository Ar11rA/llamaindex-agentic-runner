"""
LLM Factory - Creates LLM instances based on provider configuration.

Supports:
- OpenAI (via LlamaIndex)
- Anthropic (via LlamaIndex)
- Gemini Vertex AI (custom implementation with OAuth)
- Bedrock (custom implementation with bearer token)
- Cohere (via LlamaIndex)
"""

import logging
from typing import NoReturn, Optional

from llama_index.core.llms import LLM

from config.settings import Settings, LLMProvider, get_settings


def _assert_never(value: NoReturn) -> NoReturn:
    """Assert that a code path is unreachable (exhaustive match helper)."""
    raise ValueError(f"Unsupported LLM provider: {value}")

logger = logging.getLogger(__name__)


class LLMFactory:
    """Factory for creating LLM instances based on provider."""

    @classmethod
    def create(
        cls,
        provider: Optional[LLMProvider] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        settings: Optional[Settings] = None,
    ) -> LLM:
        """
        Create an LLM instance based on provider.

        Args:
            provider: LLM provider (defaults to settings.llm_provider)
            model: Model name (defaults to settings.default_model)
            temperature: Temperature (defaults to settings.default_temperature)
            settings: Settings instance (defaults to get_settings())

        Returns:
            Configured LLM instance

        Raises:
            ValueError: If provider is not supported or required credentials missing
        """
        settings = settings or get_settings()
        provider = provider or settings.llm_provider
        model = model or settings.default_model
        temperature = (
            temperature if temperature is not None else settings.default_temperature
        )

        logger.info("Creating LLM: provider=%s, model=%s", provider, model)

        match provider:
            case LLMProvider.OPENAI:
                return cls._create_openai(settings, model, temperature)
            case LLMProvider.ANTHROPIC:
                return cls._create_anthropic(settings, model, temperature)
            case LLMProvider.GEMINI_VERTEX:
                return cls._create_gemini_vertex(settings, model, temperature)
            case LLMProvider.BEDROCK:
                return cls._create_bedrock(settings, model, temperature)
            case LLMProvider.COHERE:
                return cls._create_cohere(settings, model, temperature)
            case _ as unreachable:
                _assert_never(unreachable)

    @staticmethod
    def _create_openai(settings: Settings, model: str, temperature: float) -> LLM:
        """Create OpenAI LLM."""
        from llama_index.llms.openai import OpenAI

        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required for OpenAI provider")

        return OpenAI(
            model=model,
            temperature=temperature,
            api_base=settings.openai_api_base,
            api_key=settings.openai_api_key,
        )

    @staticmethod
    def _create_anthropic(settings: Settings, model: str, temperature: float) -> LLM:
        """Create Anthropic LLM."""
        from llama_index.llms.anthropic import Anthropic

        if not settings.anthropic_api_key:
            raise ValueError("ANTHROPIC_API_KEY is required for Anthropic provider")

        # Map generic model names to Anthropic models if needed
        anthropic_model = (
            model if model.startswith("claude") else "claude-3-haiku-20240307"
        )

        return Anthropic(
            model=anthropic_model,
            temperature=temperature,
            api_key=settings.anthropic_api_key,
            base_url=settings.anthropic_api_base,
        )

    @staticmethod
    def _create_gemini_vertex(
        settings: Settings, model: str, temperature: float
    ) -> LLM:
        """Create Google Gemini LLM via Vertex AI with custom credentials."""
        from config.custom_llms import GeminiVertexLLM

        gemini_model = (
            model if model.startswith("gemini") else "gemini-2.0-flash-lite-001"
        )

        return GeminiVertexLLM(
            model=gemini_model,
            temperature=temperature,
            base_url=settings.gemini_vertex_base_url,
            access_token=settings.gemini_vertex_access_token,
            project=settings.gemini_vertex_project,
            location=settings.gemini_vertex_location,
            api_version=settings.gemini_vertex_api_version,
        )

    @staticmethod
    def _create_bedrock(settings: Settings, model: str, temperature: float) -> LLM:
        """Create AWS Bedrock LLM via AI Gateway with bearer token."""
        from config.custom_llms import BedrockGatewayLLM

        bedrock_model = model if "." in model else settings.bedrock_model_id

        return BedrockGatewayLLM(
            model=bedrock_model,
            temperature=temperature,
            endpoint_url=settings.bedrock_endpoint_url,
            region_name=settings.bedrock_region,
            bearer_token=settings.bedrock_bearer_token,
        )

    @staticmethod
    def _create_cohere(settings: Settings, model: str, temperature: float) -> LLM:
        """Create Cohere LLM."""
        from llama_index.llms.cohere import Cohere

        if not settings.cohere_api_key:
            raise ValueError("COHERE_API_KEY is required for Cohere provider")

        cohere_model = model if model.startswith("command") else settings.cohere_model

        kwargs: dict = {
            "model": cohere_model,
            "temperature": temperature,
            "api_key": settings.cohere_api_key,
        }

        # Add base URL if custom endpoint specified
        if settings.cohere_api_base:
            kwargs["api_url"] = settings.cohere_api_base

        return Cohere(**kwargs)


def create_llm(
    provider: Optional[LLMProvider] = None,
    model: Optional[str] = None,
    temperature: Optional[float] = None,
) -> LLM:
    """
    Convenience function for creating LLM instances.

    This is the primary interface for getting LLM instances in the application.

    Args:
        provider: LLM provider (defaults to settings.llm_provider)
        model: Model name (defaults to settings.default_model)
        temperature: Temperature (defaults to settings.default_temperature)

    Returns:
        Configured LLM instance
    """
    return LLMFactory.create(provider=provider, model=model, temperature=temperature)
