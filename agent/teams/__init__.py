"""
Multi-agent team registry and exports.
"""

from typing import Protocol, runtime_checkable

from teams.base import (
    BaseTeam,
    HITLPendingResult,
    CompletedResult,
    RunResult,
)
from teams.market_research_team import MarketResearchTeam
from teams.research_math_orchestrator_team import ResearchMathOrchestratorTeam


@runtime_checkable
class TeamProtocol(Protocol):
    """Protocol defining the interface for teams."""

    NAME: str
    DESCRIPTION: str

    async def run(self, user_msg: str, session_id: str | None = None) -> str: ...

    async def run_with_hitl(
        self, user_msg: str, session_id: str | None = None
    ) -> RunResult: ...

    async def resume_with_input(
        self,
        context_dict: dict,
        human_response: str,
        user_name: str = "operator",
        session_id: str | None = None,
    ) -> RunResult: ...

    async def clear_session(self, session_id: str) -> bool: ...


class TeamRegistry:
    """Registry for managing available multi-agent teams."""

    def __init__(self):
        self._teams: dict[str, TeamProtocol] = {}

    def register(self, team_cls: type) -> None:
        """Register a team class (instantiates it)."""
        instance = team_cls()
        self._teams[instance.NAME] = instance

    def get(self, team_id: str) -> TeamProtocol | None:
        """Get a team by ID."""
        return self._teams.get(team_id)

    def list_teams(self) -> list[dict]:
        """List all registered teams with their agents."""
        result = []
        for team in self._teams.values():
            # Get agent info from the underlying AgentWorkflow
            agents_info = []
            for agent_name, agent in team.workflow.agents.items():
                agents_info.append(
                    {
                        "name": agent_name,
                        "description": agent.description,
                        "can_handoff_to": agent.can_handoff_to or [],
                    }
                )

            # Format name: "market_research_team" -> "Market Research Team"
            display_name = team.NAME.replace("_", " ").title()

            result.append(
                {
                    "id": team.NAME,
                    "name": display_name,
                    "description": team.DESCRIPTION,
                    "root_agent": team.workflow.root_agent,
                    "agents": agents_info,
                }
            )
        return result


# Global team registry
team_registry = TeamRegistry()

# Register teams
team_registry.register(MarketResearchTeam)
team_registry.register(ResearchMathOrchestratorTeam)

__all__ = [
    "BaseTeam",
    "HITLPendingResult",
    "CompletedResult",
    "RunResult",
    "TeamProtocol",
    "TeamRegistry",
    "team_registry",
    "MarketResearchTeam",
    "ResearchMathOrchestratorTeam",
]
