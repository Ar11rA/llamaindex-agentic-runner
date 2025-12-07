"""
Research Math Orchestrator Team - uses research and math agents as tools.

This team uses the orchestrator pattern where a central agent delegates
tasks to specialized agents (wrapped as tools) rather than using handoffs.

Based on: https://developers.llamaindex.ai/python/examples/agent/agents_as_tools/
"""

from typing import List, Dict, Any

from llama_index.core.agent.workflow import FunctionAgent
from llama_index.llms.openai import OpenAI

from teams.base import BaseTeam
from agents import ResearchAgent, MathAgent
from config import get_settings


class ResearchMathOrchestratorTeam(BaseTeam):
    """
    An orchestrator team that uses research and math agents as tools.

    Unlike handoff-based teams, this orchestrator:
    - Has a single orchestrator agent that coordinates all work
    - Calls specialized agents as tools to complete subtasks
    - Maintains central control of the conversation flow

    Agents (as tools):
    - research: Web search capabilities via Perplexity AI
    - math: Mathematical operations (add, multiply)
    """

    NAME = "research_math_orchestrator_team"
    DESCRIPTION = (
        "An orchestrator team that can research information from the web and perform "
        "mathematical calculations. The orchestrator delegates to specialized agents."
    )

    def __init__(self, timeout: float = 600.0):
        # Initialize sub-agents before calling super().__init__
        self._research_agent = ResearchAgent()
        self._math_agent = MathAgent()
        super().__init__(timeout=timeout)

    def get_agents(self) -> List[FunctionAgent]:
        settings = get_settings()

        # Shared LLM for orchestrator
        llm = OpenAI(
            model=settings.default_model,
            temperature=settings.default_temperature,
            api_base=settings.openai_api_base,
            api_key=settings.openai_api_key,
        )

        # Wrap sub-agents as tools for the orchestrator
        research_tool = self._research_agent.as_tool()
        math_tool = self._math_agent.as_tool()

        # Orchestrator agent that delegates to specialized agents
        orchestrator = FunctionAgent(
            name="orchestrator",
            description="Central orchestrator that coordinates research and math tasks.",
            system_prompt=(
                "You are an orchestrator agent that coordinates tasks between specialized agents.\n\n"
                "You have access to:\n"
                "- call_research_agent: Delegates web research tasks to find information\n"
                "- call_math_agent: Delegates mathematical calculations\n\n"
                "Analyze the user's request and delegate to the appropriate agent(s). "
                "You can call multiple agents if needed to complete complex tasks. "
                "Synthesize the results into a coherent response for the user."
            ),
            tools=[research_tool, math_tool],
            llm=llm,
        )

        return [orchestrator]

    def get_root_agent(self) -> str:
        """The orchestrator is always the root (and only) agent."""
        return "orchestrator"

    def get_initial_state(self) -> Dict[str, Any]:
        """Initial shared state for the team."""
        return {
            "delegated_tasks": [],
        }
