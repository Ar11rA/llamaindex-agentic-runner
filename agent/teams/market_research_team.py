"""
Market Research Team - combines Research and Market agents.

This team can:
1. Research market information from the web
2. Retrieve and update market index data (with HITL for updates)
"""

from typing import List, Dict, Any

from llama_index.core.agent.workflow import FunctionAgent

from teams.base import BaseTeam
from agents import ResearchAgent, MarketAgent


class MarketResearchTeam(BaseTeam):
    """
    A multi-agent team that combines research and market data capabilities.

    Agents:
    - research: Searches the web for market information
    - market: Manages market index data (with HITL for updates)

    Flow: research ↔ market (bidirectional handoffs)
    """

    NAME = "market_research_team"
    DESCRIPTION = (
        "A multi-agent team that can research market trends from the web "
        "and manage market index data. Index updates require human confirmation."
    )

    def get_agents(self) -> List[FunctionAgent]:
        # Reuse agents from agents/ folder with handoff rules for this team
        research_agent = ResearchAgent().for_team(can_handoff_to=["market"])
        market_agent = MarketAgent().for_team(can_handoff_to=["research"])

        return [research_agent, market_agent]

    def get_root_agent(self) -> str:
        """Start with research agent - it will handoff to market when needed."""
        return "research"

    def get_initial_state(self) -> Dict[str, Any]:
        """Initial shared state for the team."""
        return {
            "research_notes": [],
            "updated_indices": [],
        }
