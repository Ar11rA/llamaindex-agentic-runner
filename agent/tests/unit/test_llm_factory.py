"""
Unit tests for LLM Factory.

Tests factory dispatch logic and provider-specific LLM creation.
All LLM imports are mocked to avoid network calls.
"""

from unittest.mock import MagicMock, patch

import pytest

from config.settings import LLMProvider, Settings


# -----------------------------------------------------------------------------
# Factory Tests
# -----------------------------------------------------------------------------


class TestLLMFactory:
    """Tests for LLMFactory class."""

    def test_factory_creates_openai_llm(self):
        """Test factory creates OpenAI LLM for OPENAI provider."""
        mock_openai = MagicMock()

        with patch("config.llm_factory.get_settings") as mock_settings:
            mock_settings.return_value = Settings(
                llm_provider=LLMProvider.OPENAI,
                openai_api_key="test-key",
                openai_api_base="https://api.openai.com/v1",
            )

            with patch(
                "llama_index.llms.openai.OpenAI", return_value=mock_openai
            ) as mock_cls:
                from config.llm_factory import LLMFactory

                LLMFactory.create(provider=LLMProvider.OPENAI)

                mock_cls.assert_called_once()
                call_kwargs = mock_cls.call_args.kwargs
                assert call_kwargs["api_key"] == "test-key"
                assert call_kwargs["api_base"] == "https://api.openai.com/v1"

    def test_factory_creates_anthropic_llm(self):
        """Test factory creates Anthropic LLM for ANTHROPIC provider."""
        mock_anthropic = MagicMock()

        with patch("config.llm_factory.get_settings") as mock_settings:
            mock_settings.return_value = Settings(
                llm_provider=LLMProvider.ANTHROPIC,
                openai_api_key="not-used",
                openai_api_base="https://api.openai.com/v1",
                anthropic_api_key="test-anthropic-key",
                anthropic_api_base="https://api.anthropic.com",
            )

            with patch(
                "llama_index.llms.anthropic.Anthropic", return_value=mock_anthropic
            ) as mock_cls:
                from config.llm_factory import LLMFactory

                LLMFactory.create(provider=LLMProvider.ANTHROPIC)

                mock_cls.assert_called_once()
                call_kwargs = mock_cls.call_args.kwargs
                assert call_kwargs["api_key"] == "test-anthropic-key"
                assert call_kwargs["base_url"] == "https://api.anthropic.com"

    def test_factory_creates_cohere_llm(self):
        """Test factory creates Cohere LLM for COHERE provider."""
        mock_cohere = MagicMock()

        with patch("config.llm_factory.get_settings") as mock_settings:
            mock_settings.return_value = Settings(
                llm_provider=LLMProvider.COHERE,
                openai_api_key="not-used",
                openai_api_base="https://api.openai.com/v1",
                cohere_api_key="test-cohere-key",
                cohere_api_base="https://cohere.example.com",
                cohere_model="command-r-plus",
            )

            with patch(
                "llama_index.llms.cohere.Cohere", return_value=mock_cohere
            ) as mock_cls:
                from config.llm_factory import LLMFactory

                LLMFactory.create(provider=LLMProvider.COHERE)

                mock_cls.assert_called_once()
                call_kwargs = mock_cls.call_args.kwargs
                assert call_kwargs["api_key"] == "test-cohere-key"
                assert call_kwargs["api_url"] == "https://cohere.example.com"

    def test_factory_creates_gemini_vertex_llm(self):
        """Test factory creates GeminiVertexLLM for GEMINI_VERTEX provider."""
        with patch("config.llm_factory.get_settings") as mock_settings:
            mock_settings.return_value = Settings(
                llm_provider=LLMProvider.GEMINI_VERTEX,
                openai_api_key="not-used",
                openai_api_base="https://api.openai.com/v1",
                gemini_vertex_base_url="https://vertex.example.com",
                gemini_vertex_access_token="test-token",
                gemini_vertex_project="test-project",
                gemini_vertex_location="us-central1",
            )

            with patch(
                "config.custom_llms.GeminiVertexLLM._create_client"
            ) as mock_create:
                mock_create.return_value = MagicMock()

                from config.llm_factory import LLMFactory

                llm = LLMFactory.create(provider=LLMProvider.GEMINI_VERTEX)

                from config.custom_llms import GeminiVertexLLM

                assert isinstance(llm, GeminiVertexLLM)
                assert llm.base_url == "https://vertex.example.com"
                assert llm.project == "test-project"

    def test_factory_creates_bedrock_llm(self):
        """Test factory creates BedrockGatewayLLM for BEDROCK provider."""
        with patch("config.llm_factory.get_settings") as mock_settings:
            mock_settings.return_value = Settings(
                llm_provider=LLMProvider.BEDROCK,
                openai_api_key="not-used",
                openai_api_base="https://api.openai.com/v1",
                bedrock_endpoint_url="https://bedrock.example.com",
                bedrock_bearer_token="test-bearer-token",
                bedrock_region="us-west-2",
                bedrock_model_id="anthropic.claude-3-sonnet",
            )

            with patch(
                "config.custom_llms.BedrockGatewayLLM._create_client"
            ) as mock_create:
                mock_create.return_value = MagicMock()

                from config.llm_factory import LLMFactory

                llm = LLMFactory.create(provider=LLMProvider.BEDROCK)

                from config.custom_llms import BedrockGatewayLLM

                assert isinstance(llm, BedrockGatewayLLM)
                assert llm.endpoint_url == "https://bedrock.example.com"
                assert llm.region_name == "us-west-2"

    def test_factory_raises_for_unsupported_provider(self):
        """Test factory raises ValueError for unsupported provider."""
        with patch("config.llm_factory.get_settings") as mock_settings:
            mock_settings.return_value = Settings(
                openai_api_key="not-used",
                openai_api_base="https://api.openai.com/v1",
            )

            from config.llm_factory import LLMFactory

            with pytest.raises(ValueError, match="Unsupported LLM provider"):
                LLMFactory.create(provider="invalid_provider")

    def test_factory_uses_default_provider_from_settings(self):
        """Test factory uses default provider from settings when not specified."""
        mock_openai = MagicMock()

        with patch("config.llm_factory.get_settings") as mock_settings:
            mock_settings.return_value = Settings(
                llm_provider=LLMProvider.OPENAI,
                openai_api_key="test-key",
                openai_api_base="https://api.openai.com/v1",
            )

            with patch(
                "llama_index.llms.openai.OpenAI", return_value=mock_openai
            ) as mock_cls:
                from config.llm_factory import LLMFactory

                # Don't specify provider - should use default from settings
                LLMFactory.create()

                mock_cls.assert_called_once()

    def test_factory_passes_model_and_temperature(self):
        """Test factory passes model and temperature to LLM constructor."""
        mock_openai = MagicMock()

        with patch("config.llm_factory.get_settings") as mock_settings:
            mock_settings.return_value = Settings(
                llm_provider=LLMProvider.OPENAI,
                openai_api_key="test-key",
                openai_api_base="https://api.openai.com/v1",
                default_model="gpt-4",
                default_temperature=0.7,
            )

            with patch(
                "llama_index.llms.openai.OpenAI", return_value=mock_openai
            ) as mock_cls:
                from config.llm_factory import LLMFactory

                LLMFactory.create(
                    provider=LLMProvider.OPENAI,
                    model="gpt-4-turbo",
                    temperature=0.9,
                )

                call_kwargs = mock_cls.call_args.kwargs
                assert call_kwargs["model"] == "gpt-4-turbo"
                assert call_kwargs["temperature"] == 0.9


# -----------------------------------------------------------------------------
# Settings Validation Tests
# -----------------------------------------------------------------------------


class TestLLMFactoryValidation:
    """Tests for factory input validation."""

    def test_openai_requires_api_key(self):
        """Test OpenAI provider raises error when API key missing."""
        with patch("config.llm_factory.get_settings") as mock_settings:
            mock_settings.return_value = Settings(
                openai_api_key=None,
                openai_api_base="https://api.openai.com/v1",
            )

            from config.llm_factory import LLMFactory

            with pytest.raises(ValueError, match="OPENAI_API_KEY is required"):
                LLMFactory.create(provider=LLMProvider.OPENAI)

    def test_anthropic_requires_api_key(self):
        """Test Anthropic provider raises error when API key missing."""
        with patch("config.llm_factory.get_settings") as mock_settings:
            mock_settings.return_value = Settings(
                openai_api_key="not-used",
                openai_api_base="https://api.openai.com/v1",
                anthropic_api_key=None,
            )

            from config.llm_factory import LLMFactory

            with pytest.raises(ValueError, match="ANTHROPIC_API_KEY is required"):
                LLMFactory.create(provider=LLMProvider.ANTHROPIC)

    def test_cohere_requires_api_key(self):
        """Test Cohere provider raises error when API key missing."""
        with patch("config.llm_factory.get_settings") as mock_settings:
            mock_settings.return_value = Settings(
                openai_api_key="not-used",
                openai_api_base="https://api.openai.com/v1",
                cohere_api_key=None,
            )

            from config.llm_factory import LLMFactory

            with pytest.raises(ValueError, match="COHERE_API_KEY is required"):
                LLMFactory.create(provider=LLMProvider.COHERE)


# -----------------------------------------------------------------------------
# Convenience Function Tests
# -----------------------------------------------------------------------------


class TestCreateLLMFunction:
    """Tests for create_llm convenience function."""

    def test_create_llm_calls_factory(self):
        """Test create_llm function calls LLMFactory.create."""
        mock_openai = MagicMock()

        with patch("config.llm_factory.get_settings") as mock_settings:
            mock_settings.return_value = Settings(
                llm_provider=LLMProvider.OPENAI,
                openai_api_key="test-key",
                openai_api_base="https://api.openai.com/v1",
            )

            with patch(
                "llama_index.llms.openai.OpenAI", return_value=mock_openai
            ) as mock_cls:
                from config.llm_factory import create_llm

                create_llm(provider=LLMProvider.OPENAI)

                mock_cls.assert_called_once()


# -----------------------------------------------------------------------------
# Model Name Mapping Tests
# -----------------------------------------------------------------------------


class TestModelNameMapping:
    """Tests for model name mapping in factory."""

    def test_anthropic_maps_generic_model_to_claude(self):
        """Test Anthropic maps non-claude model names to default Claude model."""
        mock_anthropic = MagicMock()

        with patch("config.llm_factory.get_settings") as mock_settings:
            mock_settings.return_value = Settings(
                llm_provider=LLMProvider.ANTHROPIC,
                openai_api_key="not-used",
                openai_api_base="https://api.openai.com/v1",
                anthropic_api_key="test-key",
                default_model="gpt-4",  # Not a Claude model
            )

            with patch(
                "llama_index.llms.anthropic.Anthropic", return_value=mock_anthropic
            ) as mock_cls:
                from config.llm_factory import LLMFactory

                LLMFactory.create(provider=LLMProvider.ANTHROPIC)

                call_kwargs = mock_cls.call_args.kwargs
                assert call_kwargs["model"].startswith("claude")

    def test_anthropic_keeps_claude_model_name(self):
        """Test Anthropic keeps Claude model names as-is."""
        mock_anthropic = MagicMock()

        with patch("config.llm_factory.get_settings") as mock_settings:
            mock_settings.return_value = Settings(
                llm_provider=LLMProvider.ANTHROPIC,
                openai_api_key="not-used",
                openai_api_base="https://api.openai.com/v1",
                anthropic_api_key="test-key",
            )

            with patch(
                "llama_index.llms.anthropic.Anthropic", return_value=mock_anthropic
            ) as mock_cls:
                from config.llm_factory import LLMFactory

                LLMFactory.create(
                    provider=LLMProvider.ANTHROPIC,
                    model="claude-3-opus-20240229",
                )

                call_kwargs = mock_cls.call_args.kwargs
                assert call_kwargs["model"] == "claude-3-opus-20240229"

    def test_cohere_maps_generic_model_to_command(self):
        """Test Cohere maps non-command model names to default Command model."""
        mock_cohere = MagicMock()

        with patch("config.llm_factory.get_settings") as mock_settings:
            mock_settings.return_value = Settings(
                llm_provider=LLMProvider.COHERE,
                openai_api_key="not-used",
                openai_api_base="https://api.openai.com/v1",
                cohere_api_key="test-key",
                cohere_model="command-r-plus",
                default_model="gpt-4",  # Not a Command model
            )

            with patch(
                "llama_index.llms.cohere.Cohere", return_value=mock_cohere
            ) as mock_cls:
                from config.llm_factory import LLMFactory

                LLMFactory.create(provider=LLMProvider.COHERE)

                call_kwargs = mock_cls.call_args.kwargs
                assert call_kwargs["model"].startswith("command")
