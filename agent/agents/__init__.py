from typing import Protocol, AsyncGenerator, runtime_checkable

from agents.base import BaseAgent, HITLPendingResult, CompletedResult, RunResult
from agents.math_agent import MathAgent
from agents.research_agent import ResearchAgent
from agents.market_agent import MarketAgent
from agents.writer_agent import WriterAgent
from agents.critic_agent import CriticAgent
from config import LLMProvider


@runtime_checkable
class AgentProtocol(Protocol):
    """Protocol that all agents must implement."""

    NAME: str
    DESCRIPTION: str

    async def run(self, user_msg: str, session_id: str | None = None) -> str: ...

    async def stream(
        self, user_msg: str, session_id: str | None = None
    ) -> AsyncGenerator[str, None]: ...

    async def run_with_hitl(
        self, user_msg: str, session_id: str | None = None
    ) -> RunResult: ...

    async def resume_with_input(
        self, context_dict: dict, human_response: str, user_name: str = "operator"
    ) -> RunResult: ...

    async def clear_session(self, session_id: str) -> bool: ...


class AgentRegistry:
    """Registry for managing available agents."""

    def __init__(self):
        self._agents: dict[str, AgentProtocol] = {}

    def register(self, agent: AgentProtocol) -> None:
        """Register an agent (uses agent.NAME and agent.DESCRIPTION)."""
        self._agents[agent.NAME] = agent

    def get(self, agent_id: str) -> AgentProtocol | None:
        """Get an agent by ID."""
        return self._agents.get(agent_id)

    def list_agents(self) -> list[dict]:
        """List all registered agents with their metadata."""
        return [
            {
                "id": agent.NAME,
                "name": agent.NAME.replace("_", " ").title() + " Agent",
                "description": agent.DESCRIPTION,
            }
            for agent in self._agents.values()
        ]

    def exists(self, agent_id: str) -> bool:
        """Check if an agent exists."""
        return agent_id in self._agents


# Global registry instance
registry = AgentRegistry()

# Register available agents
registry.register(MathAgent())
registry.register(
    ResearchAgent(
        provider=LLMProvider.OPENAI,
        model="gpt-4.1",
    )
)
registry.register(MarketAgent())
registry.register(
    WriterAgent(
        provider=LLMProvider.ANTHROPIC,
    )
)
registry.register(CriticAgent())

__all__ = [
    "BaseAgent",
    "AgentProtocol",
    "AgentRegistry",
    "registry",
    "MathAgent",
    "ResearchAgent",
    "MarketAgent",
    "HITLPendingResult",
    "CompletedResult",
    "RunResult",
    "WriterAgent",
    "CriticAgent",
]
