"""
Shared pytest fixtures for testing LlamaIndex Agents.

Provides mocks for:
- Settings (observability disabled, mock API keys)
- LLM calls (via factory)
- Database operations
- FastAPI test client
"""

import os
from typing import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

# Set test environment variables BEFORE importing any app modules
os.environ["OPENAI_API_KEY"] = "test-openai-key"
os.environ["OPENAI_API_BASE"] = "https://api.openai.com/v1"
os.environ["PHOENIX_ENABLED"] = "false"
os.environ["MEMORY_DATABASE_URI"] = ""
os.environ["PERPLEXITY_API_KEY"] = "test-perplexity-key"


# -----------------------------------------------------------------------------
# Settings Fixtures
# -----------------------------------------------------------------------------


@pytest.fixture
def mock_settings():
    """Override settings with test values."""
    from config.settings import Settings, LLMProvider

    return Settings(
        llm_provider=LLMProvider.OPENAI,
        openai_api_key="test-openai-key",
        openai_api_base="https://api.openai.com/v1",
        default_model="gpt-4-test",
        default_temperature=0.0,
        memory_database_uri=None,
        phoenix_enabled=False,
        perplexity_api_key="test-perplexity-key",
    )


@pytest.fixture(autouse=True)
def patch_settings(mock_settings):
    """Auto-use fixture to patch get_settings for all tests."""
    with patch("config.settings.get_settings", return_value=mock_settings):
        # Also patch in config module
        with patch("config.get_settings", return_value=mock_settings):
            # Patch in llm_factory module
            with patch("config.llm_factory.get_settings", return_value=mock_settings):
                yield mock_settings


# -----------------------------------------------------------------------------
# LLM Fixtures
# -----------------------------------------------------------------------------


@pytest.fixture
def mock_llm_response():
    """Default mock LLM response."""
    return "This is a mock LLM response."


@pytest.fixture
def mock_llm(mock_llm_response):
    """Create a mock LLM instance."""
    mock = MagicMock()

    # Mock the chat method
    mock_response = MagicMock()
    mock_response.message.content = mock_llm_response
    mock.chat.return_value = mock_response

    # Mock async chat
    mock.achat = AsyncMock(return_value=mock_response)

    # Mock complete methods
    mock.complete.return_value = MagicMock(text=mock_llm_response)
    mock.acomplete = AsyncMock(return_value=MagicMock(text=mock_llm_response))

    return mock


@pytest.fixture
def mock_openai_llm(mock_llm):
    """Mock the OpenAI LLM to return canned responses."""
    with patch("llama_index.llms.openai.OpenAI", return_value=mock_llm):
        yield mock_llm


@pytest.fixture
def mock_create_llm(mock_llm):
    """Mock the create_llm factory function to return a mock LLM."""
    with patch("config.llm_factory.create_llm", return_value=mock_llm):
        with patch("config.create_llm", return_value=mock_llm):
            yield mock_llm


@pytest.fixture(autouse=True)
def patch_llm_factory(mock_llm):
    """Auto-patch LLM factory for all tests to avoid real LLM calls."""
    # Create a mock FunctionAgent that doesn't validate LLM type
    mock_function_agent_instance = MagicMock()
    mock_function_agent_instance.run = AsyncMock(return_value="Mock response")

    # Patch OpenAI which is the default provider
    with patch("llama_index.llms.openai.OpenAI", return_value=mock_llm):
        # Patch FunctionAgent to avoid Pydantic validation of LLM type
        with patch(
            "llama_index.core.agent.workflow.FunctionAgent",
            return_value=mock_function_agent_instance,
        ):
            # Also patch in agents.base where it's imported
            with patch(
                "agents.base.FunctionAgent",
                return_value=mock_function_agent_instance,
            ):
                yield mock_llm


# -----------------------------------------------------------------------------
# Database Fixtures
# -----------------------------------------------------------------------------


@pytest.fixture
def mock_memory():
    """Mock Memory object."""
    memory = MagicMock()
    memory.get.return_value = []
    memory.put = MagicMock()
    memory.areset = AsyncMock()
    return memory


@pytest.fixture
def mock_db_manager(mock_memory):
    """Mock the DatabaseManager singleton."""
    from config.database import DatabaseManager

    mock_manager = MagicMock(spec=DatabaseManager)

    # Memory methods
    mock_manager.get_memory.return_value = mock_memory
    mock_manager.clear_memory = AsyncMock(return_value=True)

    # Workflow state methods
    mock_manager.save_workflow_state = AsyncMock()
    mock_manager.get_workflow_state = AsyncMock(return_value=None)
    mock_manager.update_workflow_status = AsyncMock()
    mock_manager.delete_workflow_state = AsyncMock(return_value=True)

    # Flow run methods
    mock_manager.create_flow_run = AsyncMock()
    mock_manager.update_flow_run_status = AsyncMock()
    mock_manager.get_flow_run = AsyncMock(return_value=None)
    mock_manager.add_flow_step = AsyncMock()
    mock_manager.get_flow_steps = AsyncMock(return_value=[])

    # Connection methods
    mock_manager.connect = AsyncMock()
    mock_manager.disconnect = AsyncMock()
    mock_manager.engine = None

    with patch("config.database.db_manager", mock_manager):
        with patch("config.db_manager", mock_manager):
            yield mock_manager


# -----------------------------------------------------------------------------
# Agent Fixtures
# -----------------------------------------------------------------------------


@pytest.fixture
def mock_agent_run():
    """Mock agent.run() to return a canned response."""

    async def mock_run(*args, **kwargs):
        return "Mock agent response"

    return mock_run


@pytest.fixture
def mock_function_agent(mock_agent_run):
    """Mock FunctionAgent for testing."""
    mock_agent = MagicMock()
    mock_agent.run = AsyncMock(return_value="Mock agent response")

    # Mock the handler for streaming
    mock_handler = MagicMock()
    mock_handler.stream_events = MagicMock(return_value=async_generator_empty())
    mock_handler.ctx = MagicMock()
    mock_handler.ctx.to_dict.return_value = {}

    with patch(
        "llama_index.core.agent.workflow.FunctionAgent", return_value=mock_agent
    ):
        yield mock_agent


async def async_generator_empty():
    """Helper for empty async generator."""
    return
    yield  # Makes this a generator


# -----------------------------------------------------------------------------
# FastAPI Test Client Fixtures
# -----------------------------------------------------------------------------


@pytest.fixture
def test_client(mock_db_manager, mock_settings):
    """FastAPI test client with mocked dependencies."""
    # Import app after mocks are set up
    from main import app

    with TestClient(app) as client:
        yield client


@pytest.fixture
def async_test_client(mock_db_manager, mock_settings):
    """Async test client for async endpoint testing."""
    from httpx import ASGITransport, AsyncClient

    from main import app

    async def get_client() -> AsyncGenerator:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            yield client

    return get_client


# -----------------------------------------------------------------------------
# Perplexity/Research Fixtures
# -----------------------------------------------------------------------------


@pytest.fixture
def mock_perplexity_response():
    """Mock response from Perplexity API."""
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "Mock search result from Perplexity"
    return mock_response


@pytest.fixture
def mock_perplexity_client(mock_perplexity_response):
    """Mock the OpenAI client used for Perplexity."""
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = mock_perplexity_response

    with patch("openai.OpenAI", return_value=mock_client):
        yield mock_client


# -----------------------------------------------------------------------------
# Flow/Team Fixtures
# -----------------------------------------------------------------------------


@pytest.fixture
def mock_flow_result():
    """Mock flow execution result."""
    return {"result": "Mock flow completed", "steps": 3}


@pytest.fixture
def mock_team_result():
    """Mock team execution result."""
    return "Mock team response"
