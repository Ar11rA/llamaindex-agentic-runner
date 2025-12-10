import logging
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, List, Callable, AsyncGenerator, Any, Union

from llama_index.core.agent.workflow import FunctionAgent
from llama_index.core.agent.workflow.workflow_events import AgentStream
from llama_index.core.llms import LLM
from llama_index.core.workflow import Context, InputRequiredEvent, HumanResponseEvent

from config import get_settings, db_manager, LLMProvider, create_llm


@dataclass
class HITLPendingResult:
    """Returned when workflow is paused waiting for human input."""

    workflow_id: str
    prompt: str
    context_dict: dict
    user_name: str


@dataclass
class CompletedResult:
    """Returned when workflow completes successfully."""

    response: str


# Union type for run results
RunResult = Union[HITLPendingResult, CompletedResult]


class BaseAgent(ABC):
    """
    Abstract base class for all agents.

    Subclasses must define:
        - NAME: Agent identifier (used for table naming, registry, etc.)
        - DESCRIPTION: Human-readable description
        - DEFAULT_SYSTEM_PROMPT: Default system prompt for the agent
        - get_tools(): Method returning the list of tools

    Supports Human-in-the-Loop (HITL) via context serialization.
    Supports multiple LLM providers via the factory pattern.
    """

    NAME: str
    DESCRIPTION: str
    DEFAULT_SYSTEM_PROMPT: str

    def __init__(
        self,
        provider: Optional[LLMProvider] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        system_prompt: Optional[str] = None,
        timeout: float = 600.0,  # 10 min default for HITL
        llm: Optional[LLM] = None,  # Allow injecting custom LLM
    ):
        self._logger = logging.getLogger(f"agents.{self.NAME}")
        settings = get_settings()

        self._provider = provider or settings.llm_provider
        self._model = model or settings.default_model
        self._temperature = (
            temperature if temperature is not None else settings.default_temperature
        )

        # Use injected LLM or create via factory
        self.llm = llm or create_llm(
            provider=self._provider,
            model=self._model,
            temperature=self._temperature,
        )

        self.system_prompt = system_prompt or self.DEFAULT_SYSTEM_PROMPT
        self.tools = self.get_tools()
        self._timeout = timeout

        self.agent = FunctionAgent(
            name=self.NAME,
            description=self.DESCRIPTION,
            tools=self.tools,
            llm=self.llm,
            system_prompt=self.system_prompt,
            timeout=timeout,
        )

        self._logger.info(
            "Initialized with provider=%s, model=%s, temperature=%s, timeout=%s",
            self._provider,
            self._model,
            self._temperature,
            timeout,
        )

    @abstractmethod
    def get_tools(self) -> List[Callable[..., Any]]:
        """Return the list of tools for this agent. Must be implemented by subclasses."""
        ...

    def _get_memory(self, session_id: Optional[str]):
        """Get memory for a session if session_id is provided."""
        if session_id:
            return db_manager.get_memory(session_id, self.NAME)
        return None

    def get_agent(self) -> FunctionAgent:
        """Return the underlying FunctionAgent instance."""
        return self.agent

    def for_team(self, can_handoff_to: Optional[List[str]] = None) -> FunctionAgent:
        """
        Return a FunctionAgent configured for use in a team (AgentWorkflow).

        Args:
            can_handoff_to: List of agent names this agent can delegate to.

        Returns:
            A FunctionAgent with name, description, and handoff rules configured.
        """
        return FunctionAgent(
            name=self.NAME,
            description=self.DESCRIPTION,
            tools=self.tools,
            llm=self.llm,
            system_prompt=self.system_prompt,
            timeout=self._timeout,
            can_handoff_to=can_handoff_to or [],
        )

    def as_tool(self) -> Callable[..., Any]:
        """
        Wrap this agent as a callable tool for use in an orchestrator pattern.

        The orchestrator can call this agent as a tool, delegating tasks to it.
        Based on: https://developers.llamaindex.ai/python/examples/agent/agents_as_tools/

        Returns:
            A callable async function that runs the agent with the given input.
        """

        async def agent_tool(input: str) -> str:
            """Run the agent with the given input and return the response."""
            return await self.run(input)

        # Set metadata for the tool
        agent_tool.__name__ = f"call_{self.NAME}_agent"
        agent_tool.__doc__ = (
            f"{self.DESCRIPTION}\n\n"
            f"Use this tool to delegate tasks to the {self.NAME} agent."
        )

        return agent_tool

    # ─────────────────────────────────────────────────────────────
    # HITL-AWARE METHODS
    # ─────────────────────────────────────────────────────────────

    async def run_with_hitl(
        self,
        user_msg: str,
        session_id: Optional[str] = None,
    ) -> RunResult:
        """
        Run the agent, handling HITL interruptions.

        Returns:
            - CompletedResult if workflow finishes
            - HITLPendingResult if human input is required
        """
        self._logger.info("Session %s | HITL Query: %s", session_id, user_msg)

        memory = self._get_memory(session_id)
        handler = self.agent.run(user_msg=user_msg, memory=memory)

        async for event in handler.stream_events():
            if isinstance(event, InputRequiredEvent):
                # HITL triggered - serialize context
                ctx_dict = handler.ctx.to_dict()
                workflow_id = str(uuid.uuid4())

                self._logger.info(
                    "Session %s | HITL triggered, workflow_id=%s, prompt=%s",
                    session_id,
                    workflow_id,
                    event.prefix,
                )

                return HITLPendingResult(
                    workflow_id=workflow_id,
                    prompt=event.prefix,
                    context_dict=ctx_dict,
                    user_name=getattr(event, "user_name", "operator"),
                )

        # Workflow completed without HITL
        response = await handler
        response_str = str(response)

        self._logger.info("Session %s | HITL Response: %s", session_id, response_str)
        return CompletedResult(response=response_str)

    async def resume_with_input(
        self,
        context_dict: dict,
        human_response: str,
        user_name: str = "operator",
        session_id: Optional[str] = None,
    ) -> RunResult:
        """
        Resume a paused workflow with human input.

        Args:
            context_dict: Serialized context from HITLPendingResult
            human_response: The human's response
            user_name: Must match the user_name in InputRequiredEvent
            session_id: Session ID for restoring memory

        Returns:
            - CompletedResult if workflow finishes
            - HITLPendingResult if another human input is required
        """
        self._logger.info("Resuming workflow with response: %s", human_response)

        # Restore context from serialized state
        ctx = Context.from_dict(self.agent, context_dict)

        # Restore memory (it's not serializable, so we need to set it manually)
        # See: "Skipping serialization of known unserializable key: memory"
        memory = self._get_memory(session_id)
        if memory:
            await ctx.store.set("memory", memory)

        # Start the workflow with restored context - it will resume from where it paused
        handler = self.agent.run(ctx=ctx)

        # Send the human response event to the now-running workflow
        handler.ctx.send_event(
            HumanResponseEvent(
                response=human_response,
                user_name=user_name,
            )
        )

        async for event in handler.stream_events():
            if isinstance(event, InputRequiredEvent):
                # Another HITL triggered
                ctx_dict = handler.ctx.to_dict()
                workflow_id = str(uuid.uuid4())

                self._logger.info(
                    "HITL triggered again, workflow_id=%s, prompt=%s",
                    workflow_id,
                    event.prefix,
                )

                return HITLPendingResult(
                    workflow_id=workflow_id,
                    prompt=event.prefix,
                    context_dict=ctx_dict,
                    user_name=getattr(event, "user_name", "operator"),
                )

        # Workflow completed
        response = await handler
        response_str = str(response)

        self._logger.info("Resumed workflow completed: %s", response_str)
        return CompletedResult(response=response_str)

    # ─────────────────────────────────────────────────────────────
    # SIMPLE METHODS (for non-HITL agents)
    # ─────────────────────────────────────────────────────────────

    async def run(self, user_msg: str, session_id: Optional[str] = None) -> str:
        """Run the agent (simple mode, no HITL support)."""
        self._logger.info("Session %s | Query: %s", session_id, user_msg)

        memory = self._get_memory(session_id)
        response = await self.agent.run(user_msg=user_msg, memory=memory)
        response_str = str(response)

        self._logger.info("Session %s | Response: %s", session_id, response_str)
        return response_str

    async def stream(
        self, user_msg: str, session_id: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        """Stream the agent response (simple mode, no HITL support)."""
        self._logger.info("Session %s | Streaming query: %s", session_id, user_msg)

        memory = self._get_memory(session_id)
        handler = self.agent.run(user_msg=user_msg, memory=memory)
        full_response = ""

        async for event in handler.stream_events():
            if isinstance(event, AgentStream):
                full_response += event.delta
                yield event.delta

        self._logger.info(
            "Session %s | Streamed response: %s", session_id, full_response
        )

    async def clear_session(self, session_id: str) -> bool:
        """Clear memory for a specific session."""
        cleared = await db_manager.clear_memory(session_id, self.NAME)
        self._logger.info("Cleared memory for session: %s", session_id)
        return cleared
