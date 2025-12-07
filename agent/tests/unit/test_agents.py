"""
Unit tests for agent classes.

Tests agent initialization, configuration, and tool registration.
LLM calls are mocked.
"""

from unittest.mock import patch

import pytest


# -----------------------------------------------------------------------------
# MathAgent Tests
# -----------------------------------------------------------------------------


class TestMathAgent:
    """Tests for MathAgent class."""

    def test_math_agent_has_correct_name(self):
        """Test MathAgent has correct NAME attribute."""
        from agents.math_agent import MathAgent

        assert MathAgent.NAME == "math"

    def test_math_agent_has_description(self):
        """Test MathAgent has a description."""
        from agents.math_agent import MathAgent

        assert MathAgent.DESCRIPTION is not None
        assert len(MathAgent.DESCRIPTION) > 0

    def test_math_agent_get_tools_returns_list(self):
        """Test get_tools returns a list of callables."""
        from agents.math_agent import MathAgent

        with patch("llama_index.llms.openai.OpenAI"):
            agent = MathAgent()
            tools = agent.get_tools()

        assert isinstance(tools, list)
        assert len(tools) == 2  # add and multiply

    def test_math_agent_tools_are_callable(self):
        """Test that returned tools are callable."""
        from agents.math_agent import MathAgent

        with patch("llama_index.llms.openai.OpenAI"):
            agent = MathAgent()
            tools = agent.get_tools()

        for tool in tools:
            assert callable(tool)

    def test_math_agent_has_add_tool(self):
        """Test MathAgent includes add tool."""
        from agents.math_agent import MathAgent
        from tools.math_tools import add

        with patch("llama_index.llms.openai.OpenAI"):
            agent = MathAgent()
            tools = agent.get_tools()

        assert add in tools

    def test_math_agent_has_multiply_tool(self):
        """Test MathAgent includes multiply tool."""
        from agents.math_agent import MathAgent
        from tools.math_tools import multiply

        with patch("llama_index.llms.openai.OpenAI"):
            agent = MathAgent()
            tools = agent.get_tools()

        assert multiply in tools


# -----------------------------------------------------------------------------
# ResearchAgent Tests
# -----------------------------------------------------------------------------


class TestResearchAgent:
    """Tests for ResearchAgent class."""

    def test_research_agent_has_correct_name(self):
        """Test ResearchAgent has correct NAME attribute."""
        from agents.research_agent import ResearchAgent

        assert ResearchAgent.NAME == "research"

    def test_research_agent_has_description(self):
        """Test ResearchAgent has a description."""
        from agents.research_agent import ResearchAgent

        assert ResearchAgent.DESCRIPTION is not None
        assert len(ResearchAgent.DESCRIPTION) > 0

    def test_research_agent_get_tools_returns_list(self):
        """Test get_tools returns a list."""
        from agents.research_agent import ResearchAgent

        with patch("llama_index.llms.openai.OpenAI"):
            agent = ResearchAgent()
            tools = agent.get_tools()

        assert isinstance(tools, list)
        assert len(tools) >= 1  # At least web_search

    def test_research_agent_has_web_search_tool(self):
        """Test ResearchAgent includes web_search tool."""
        from agents.research_agent import ResearchAgent
        from tools.research_tools import web_search

        with patch("llama_index.llms.openai.OpenAI"):
            agent = ResearchAgent()
            tools = agent.get_tools()

        assert web_search in tools


# -----------------------------------------------------------------------------
# MarketAgent Tests
# -----------------------------------------------------------------------------


class TestMarketAgent:
    """Tests for MarketAgent class."""

    def test_market_agent_has_correct_name(self):
        """Test MarketAgent has correct NAME attribute."""
        from agents.market_agent import MarketAgent

        assert MarketAgent.NAME == "market"

    def test_market_agent_has_description(self):
        """Test MarketAgent has a description."""
        from agents.market_agent import MarketAgent

        assert MarketAgent.DESCRIPTION is not None

    def test_market_agent_get_tools_returns_list(self):
        """Test get_tools returns a list."""
        from agents.market_agent import MarketAgent

        with patch("llama_index.llms.openai.OpenAI"):
            agent = MarketAgent()
            tools = agent.get_tools()

        assert isinstance(tools, list)
        assert len(tools) >= 2  # get_index and push_index


# -----------------------------------------------------------------------------
# WriterAgent Tests
# -----------------------------------------------------------------------------


class TestWriterAgent:
    """Tests for WriterAgent class."""

    def test_writer_agent_has_correct_name(self):
        """Test WriterAgent has correct NAME attribute."""
        from agents.writer_agent import WriterAgent

        assert WriterAgent.NAME == "writer"

    def test_writer_agent_has_description(self):
        """Test WriterAgent has a description."""
        from agents.writer_agent import WriterAgent

        assert WriterAgent.DESCRIPTION is not None

    def test_writer_agent_has_no_tools(self):
        """Test WriterAgent has no tools (writing is LLM capability)."""
        from agents.writer_agent import WriterAgent

        with patch("llama_index.llms.openai.OpenAI"):
            agent = WriterAgent()
            tools = agent.get_tools()

        assert isinstance(tools, list)
        assert len(tools) == 0  # No tools, just LLM


# -----------------------------------------------------------------------------
# CriticAgent Tests
# -----------------------------------------------------------------------------


class TestCriticAgent:
    """Tests for CriticAgent class."""

    def test_critic_agent_has_correct_name(self):
        """Test CriticAgent has correct NAME attribute."""
        from agents.critic_agent import CriticAgent

        assert CriticAgent.NAME == "critic"

    def test_critic_agent_has_description(self):
        """Test CriticAgent has a description."""
        from agents.critic_agent import CriticAgent

        assert CriticAgent.DESCRIPTION is not None

    def test_critic_agent_has_no_tools(self):
        """Test CriticAgent has no tools (critique is LLM capability)."""
        from agents.critic_agent import CriticAgent

        with patch("llama_index.llms.openai.OpenAI"):
            agent = CriticAgent()
            tools = agent.get_tools()

        assert isinstance(tools, list)
        assert len(tools) == 0


# -----------------------------------------------------------------------------
# BaseAgent Tests
# -----------------------------------------------------------------------------


class TestBaseAgent:
    """Tests for BaseAgent abstract class."""

    def test_base_agent_requires_name(self):
        """Test that BaseAgent subclass requires NAME."""
        from agents.base import BaseAgent

        class InvalidAgent(BaseAgent):
            DESCRIPTION = "Test"

            def get_tools(self):
                return []

        # Should raise error due to missing NAME
        with pytest.raises(AttributeError):
            with patch("llama_index.llms.openai.OpenAI"):
                InvalidAgent()

    def test_base_agent_requires_description(self):
        """Test that BaseAgent subclass requires DESCRIPTION."""
        from agents.base import BaseAgent

        class InvalidAgent(BaseAgent):
            NAME = "test"

            def get_tools(self):
                return []

        # Should raise error due to missing DESCRIPTION
        with pytest.raises(AttributeError):
            with patch("llama_index.llms.openai.OpenAI"):
                InvalidAgent()


# -----------------------------------------------------------------------------
# Agent Registry Tests
# -----------------------------------------------------------------------------


class TestAgentRegistry:
    """Tests for agent registry."""

    def test_registry_contains_math_agent(self):
        """Test registry contains math agent."""
        from agents import registry

        assert registry.get("math") is not None

    def test_registry_contains_research_agent(self):
        """Test registry contains research agent."""
        from agents import registry

        assert registry.get("research") is not None

    def test_registry_contains_market_agent(self):
        """Test registry contains market agent."""
        from agents import registry

        assert registry.get("market") is not None

    def test_registry_list_agents_returns_list(self):
        """Test list_agents returns a list."""
        from agents import registry

        agents = registry.list_agents()
        assert isinstance(agents, list)
        assert len(agents) >= 3  # At least math, research, market

    def test_registry_get_unknown_returns_none(self):
        """Test getting unknown agent returns None."""
        from agents import registry

        result = registry.get("unknown_agent_xyz")
        assert result is None
