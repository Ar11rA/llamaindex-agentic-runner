"""
Base class for multi-agent teams using LlamaIndex AgentWorkflow.

Key constraints from AgentWorkflow source:
- All agents MUST have unique name and description
- initial_state is team-level, NOT per-agent
- Memory is SHARED across all agents in the team
"""

import logging
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, List, Dict, Any, Union, AsyncGenerator

from llama_index.core.agent.workflow import AgentWorkflow, FunctionAgent
from llama_index.core.agent.workflow.workflow_events import AgentStream
from llama_index.core.workflow import Context, InputRequiredEvent, HumanResponseEvent

from config import db_manager


@dataclass
class HITLPendingResult:
    """Returned when team is paused waiting for human input."""

    workflow_id: str
    prompt: str
    context_dict: dict
    user_name: str
    active_agent: Optional[str] = None  # Which agent triggered HITL


@dataclass
class CompletedResult:
    """Returned when team completes successfully."""

    response: str
    responding_agents: Optional[List[str]] = None  # Agents that participated


# Union type for run results
RunResult = Union[HITLPendingResult, CompletedResult]


class BaseTeam(ABC):
    """
    Abstract base class for multi-agent teams.

    Subclasses must define:
        - NAME: Team identifier (used for table naming, registry, etc.)
        - DESCRIPTION: Human-readable description
        - get_agents(): Returns list of configured FunctionAgents
        - get_root_agent(): Returns the name of the starting agent
        - get_initial_state(): (optional) Returns shared initial state

    Each agent returned by get_agents() MUST have:
        - name: Unique identifier
        - description: What the agent does
        - can_handoff_to: List of agent names it can delegate to
    """

    NAME: str
    DESCRIPTION: str

    def __init__(self, timeout: float = 600.0):
        self._logger = logging.getLogger(f"teams.{self.NAME}")
        self._timeout = timeout

        # Get agents from subclass
        agents = self.get_agents()

        # Validate agents have name and description (required by AgentWorkflow)
        for agent in agents:
            if not agent.name or agent.name == "Agent":
                raise ValueError("Each agent must have a unique name")
            if (
                not agent.description
                or agent.description == "An agent that can perform a task"
            ):
                raise ValueError(f"Agent '{agent.name}' must have a description")

        # Build AgentWorkflow (LlamaIndex's multi-agent orchestrator)
        self.workflow = AgentWorkflow(
            agents=agents,
            root_agent=self.get_root_agent(),
            initial_state=self.get_initial_state(),
            timeout=timeout,
        )

        self._logger.info(
            "Team initialized: agents=%s, root=%s",
            [a.name for a in agents],
            self.get_root_agent(),
        )

    @abstractmethod
    def get_agents(self) -> List[FunctionAgent]:
        """
        Return configured FunctionAgent instances.

        Each agent MUST have:
        - name: Unique identifier
        - description: What the agent does
        - can_handoff_to: List of agent names it can delegate to
        """
        ...

    @abstractmethod
    def get_root_agent(self) -> str:
        """Return the name of the starting agent."""
        ...

    def get_initial_state(self) -> Dict[str, Any]:
        """
        Return initial state shared by ALL agents.
        Override in subclass to provide team-specific state.
        """
        return {}

    def _get_memory(self, session_id: Optional[str]):
        """Get SHARED memory for the entire team."""
        if session_id:
            # Memory table named after team, not individual agents
            return db_manager.get_memory(session_id, self.NAME)
        return None

    # ─────────────────────────────────────────────────────────────
    # HITL-AWARE METHODS
    # ─────────────────────────────────────────────────────────────

    async def run_with_hitl(
        self,
        user_msg: str,
        session_id: Optional[str] = None,
    ) -> RunResult:
        """
        Run the team, handling HITL interruptions.

        Returns:
            - CompletedResult if team finishes (with responding_agents)
            - HITLPendingResult if human input is required
        """
        self._logger.info("Session %s | Query: %s", session_id, user_msg)

        memory = self._get_memory(session_id)
        handler = self.workflow.run(user_msg=user_msg, memory=memory)

        # Track all agents that respond during this team run
        responding_agents: set[str] = set()

        async for event in handler.stream_events():
            # Track current agent
            try:
                current_agent = await handler.ctx.store.get(
                    "current_agent_name", default=None
                )
                if current_agent:
                    responding_agents.add(current_agent)
            except Exception:
                pass

            if isinstance(event, InputRequiredEvent):
                # HITL triggered - serialize context
                ctx_dict = handler.ctx.to_dict()
                workflow_id = str(uuid.uuid4())

                # Get current agent
                active_agent = None
                try:
                    active_agent = await handler.ctx.store.get(
                        "current_agent_name", default=None
                    )
                except Exception:
                    pass

                self._logger.info(
                    "Session %s | HITL triggered, workflow_id=%s, agent=%s, prompt=%s",
                    session_id,
                    workflow_id,
                    active_agent,
                    event.prefix,
                )

                return HITLPendingResult(
                    workflow_id=workflow_id,
                    prompt=event.prefix,
                    context_dict=ctx_dict,
                    user_name=getattr(event, "user_name", "operator"),
                    active_agent=active_agent,
                )

        # Team completed without HITL
        response = await handler
        response_str = str(response)

        self._logger.info(
            "Session %s | Response: %s | Agents: %s",
            session_id,
            response_str,
            list(responding_agents),
        )
        return CompletedResult(
            response=response_str,
            responding_agents=list(responding_agents) if responding_agents else None,
        )

    async def resume_with_input(
        self,
        context_dict: dict,
        human_response: str,
        user_name: str = "operator",
        session_id: Optional[str] = None,
    ) -> RunResult:
        """
        Resume a paused team with human input.

        Args:
            context_dict: Serialized context from HITLPendingResult
            human_response: The human's response
            user_name: Must match the user_name in InputRequiredEvent
            session_id: Session ID for restoring memory

        Returns:
            - CompletedResult if team finishes
            - HITLPendingResult if another human input is required
        """
        self._logger.info("Resuming team with response: %s", human_response)

        # Restore context from serialized state
        ctx = Context.from_dict(self.workflow, context_dict)

        # Restore memory (it's not serializable, so we need to set it manually)
        memory = self._get_memory(session_id)
        if memory:
            await ctx.store.set("memory", memory)

        # Start the workflow with restored context
        handler = self.workflow.run(ctx=ctx)

        # Send the human response event to the now-running workflow
        handler.ctx.send_event(
            HumanResponseEvent(
                response=human_response,
                user_name=user_name,
            )
        )

        # Track agents that respond during resume
        responding_agents: set[str] = set()

        async for event in handler.stream_events():
            # Track current agent
            try:
                current_agent = await handler.ctx.store.get(
                    "current_agent_name", default=None
                )
                if current_agent:
                    responding_agents.add(current_agent)
            except Exception:
                pass

            if isinstance(event, InputRequiredEvent):
                # Another HITL triggered
                ctx_dict = handler.ctx.to_dict()
                workflow_id = str(uuid.uuid4())

                active_agent = None
                try:
                    active_agent = await handler.ctx.store.get(
                        "current_agent_name", default=None
                    )
                except Exception:
                    pass

                self._logger.info(
                    "HITL triggered again, workflow_id=%s, agent=%s, prompt=%s",
                    workflow_id,
                    active_agent,
                    event.prefix,
                )

                return HITLPendingResult(
                    workflow_id=workflow_id,
                    prompt=event.prefix,
                    context_dict=ctx_dict,
                    user_name=getattr(event, "user_name", "operator"),
                    active_agent=active_agent,
                )

        # Team completed
        response = await handler
        response_str = str(response)

        self._logger.info(
            "Resumed team completed: %s | Agents: %s",
            response_str,
            list(responding_agents),
        )
        return CompletedResult(
            response=response_str,
            responding_agents=list(responding_agents) if responding_agents else None,
        )

    # ─────────────────────────────────────────────────────────────
    # SIMPLE METHODS (for non-HITL teams)
    # ─────────────────────────────────────────────────────────────

    async def run(self, user_msg: str, session_id: Optional[str] = None) -> str:
        """Run the team (simple mode, no HITL support)."""
        self._logger.info("Session %s | Query: %s", session_id, user_msg)

        memory = self._get_memory(session_id)
        response = await self.workflow.run(user_msg=user_msg, memory=memory)
        response_str = str(response)

        self._logger.info("Session %s | Response: %s", session_id, response_str)
        return response_str

    async def stream(
        self, user_msg: str, session_id: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        """Stream the team response."""
        self._logger.info("Session %s | Streaming query: %s", session_id, user_msg)

        memory = self._get_memory(session_id)
        handler = self.workflow.run(user_msg=user_msg, memory=memory)
        full_response = ""

        async for event in handler.stream_events():
            if isinstance(event, AgentStream):
                full_response += event.delta
                yield event.delta
            elif isinstance(event, InputRequiredEvent):
                # For streaming, yield HITL prompt as special event
                yield f"\n[HITL_REQUIRED: {event.prefix}]\n"

        self._logger.info(
            "Session %s | Streamed response: %s", session_id, full_response
        )

    async def clear_session(self, session_id: str) -> bool:
        """Clear memory for a specific session."""
        cleared = await db_manager.clear_memory(session_id, self.NAME)
        self._logger.info("Cleared memory for session: %s", session_id)
        return cleared
