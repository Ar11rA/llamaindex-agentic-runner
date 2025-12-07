"""
Base class for LlamaIndex event-driven Workflows.

Based on: https://developers.llamaindex.ai/python/llamaagents/workflows/

Key concepts:
- Workflows are event-driven and step-based
- Steps are decorated with @step and triggered by Events
- StartEvent begins the flow, StopEvent ends it
"""

import asyncio
import logging
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional, Any, Union, AsyncGenerator

from llama_index.core.workflow import (
    Workflow,
    Context,
)
from llama_index.core.workflow.events import InputRequiredEvent, HumanResponseEvent

from config import db_manager
from config.database import FlowRunStatus


@dataclass
class HITLPendingResult:
    """Returned when flow is paused waiting for human input."""

    workflow_id: str
    prompt: str
    context_dict: dict
    user_name: str


@dataclass
class CompletedResult:
    """Returned when flow completes successfully."""

    response: Any


# Union type for run results
FlowResult = Union[HITLPendingResult, CompletedResult]


class BaseFlow(Workflow):
    """
    Abstract base class for event-driven workflows.

    Subclasses must define:
        - NAME: Flow identifier (used for registry, memory tables, etc.)
        - DESCRIPTION: Human-readable description
        - Implement steps using @step decorator

    Provides:
        - execute(): Simple async execution
        - stream_events(): Streaming execution with events
        - run_with_hitl(): HITL-aware execution
        - resume_with_input(): Resume from HITL pause
    """

    NAME: str
    DESCRIPTION: str

    def __init__(self, timeout: float = 600.0, verbose: bool = False):
        super().__init__(timeout=timeout, verbose=verbose)
        self._logger = logging.getLogger(f"flows.{self.NAME}")
        self._logger.info("Flow initialized: timeout=%s", timeout)

    def _get_memory(self, session_id: Optional[str]):
        """Get memory for a session if session_id is provided."""
        if session_id:
            return db_manager.get_memory(session_id, self.NAME)
        return None

    # ─────────────────────────────────────────────────────────────
    # DB LOGGING HELPERS
    # ─────────────────────────────────────────────────────────────

    def _serialize_event_for_db(self, event: Any, max_len: int = 10000) -> dict:
        """Serialize event for DB storage with truncation for large content."""
        data = {"type": type(event).__name__}

        # Get all fields from Pydantic models
        if hasattr(event, "model_fields"):
            for field in event.model_fields:
                value = getattr(event, field, None)
                if isinstance(value, str) and len(value) > max_len:
                    data[field] = value[:max_len] + "...[truncated]"
                    data[f"{field}_length"] = len(value)
                elif isinstance(value, (int, float, bool, type(None))):
                    data[field] = value
                elif isinstance(value, dict):
                    data[field] = value
                elif isinstance(value, list):
                    data[field] = value[:50]  # Limit list items
                else:
                    data[field] = str(value)

        # Handle result attribute (common in StopEvent)
        if hasattr(event, "result"):
            result = event.result
            if isinstance(result, str) and len(result) > max_len:
                data["result"] = result[:max_len] + "...[truncated]"
                data["result_length"] = len(result)
            elif isinstance(result, dict):
                data["result"] = result
            else:
                data["result"] = result

        return data

    def _log_step_async(
        self,
        run_id: str,
        step_index: int,
        event: Any,
        started_at: datetime,
    ) -> None:
        """Fire-and-forget: log a step to DB."""
        now = datetime.now(timezone.utc)
        event_type = type(event).__name__
        event_data = self._serialize_event_for_db(event)

        # Determine step name from event attributes or type
        step_name = event_data.get("step_name", event_type)

        # Determine status from event type
        status = "completed"
        if event_type == "StepStartedEvent":
            status = "started"

        duration_ms = int((now - started_at).total_seconds() * 1000)

        asyncio.create_task(
            db_manager.add_flow_step(
                run_id=run_id,
                step_id=str(uuid.uuid4()),
                step_name=step_name,
                step_index=step_index,
                status=status,
                event_type=event_type,
                event_data=event_data,
                started_at=started_at,
                completed_at=now if status == "completed" else None,
                duration_ms=duration_ms,
            )
        )

    # ─────────────────────────────────────────────────────────────
    # EXECUTION METHODS WITH DB LOGGING
    # ─────────────────────────────────────────────────────────────

    async def stream_flow_events_with_logging(
        self,
        run_id: Optional[str] = None,
        session_id: Optional[str] = None,
        **kwargs: Any,
    ) -> AsyncGenerator[tuple[str, Any], None]:
        """
        Stream events from flow execution with DB logging.

        This wraps stream_flow_events() and logs each event to the database
        asynchronously (fire-and-forget).

        Args:
            run_id: Optional run ID (auto-generated if not provided)
            session_id: Optional session ID for memory persistence
            **kwargs: Arguments passed to StartEvent

        Yields:
            Tuple of (run_id, event) - run_id is included so callers can reference it
        """
        run_id = run_id or str(uuid.uuid4())
        started_at = datetime.now(timezone.utc)
        step_index = 0
        final_result = None

        self._logger.info(
            "Session %s | Run %s | Starting flow with logging: %s",
            session_id,
            run_id,
            kwargs,
        )

        # Create run record
        await db_manager.create_flow_run(
            run_id=run_id,
            flow_id=self.NAME,
            input_data=kwargs,
            session_id=session_id,
        )

        # Update status to running
        await db_manager.update_flow_run_status(run_id, FlowRunStatus.RUNNING)

        try:
            handler = self.run(**kwargs, _session_id=session_id)

            async for event in handler.stream_events():
                step_index += 1

                # Fire-and-forget DB logging
                self._log_step_async(run_id, step_index, event, started_at)

                # Yield event to caller
                yield (run_id, event)

                # Capture final result
                event_type = type(event).__name__
                if event_type == "StopEvent" and hasattr(event, "result"):
                    final_result = event.result

            # Get handler result if not captured from StopEvent
            if final_result is None:
                final_result = await handler

            # Mark completed
            result_str = str(final_result) if final_result else None
            asyncio.create_task(
                db_manager.update_flow_run_status(
                    run_id,
                    FlowRunStatus.COMPLETED,
                    result=result_str,
                    metadata={"total_steps": step_index},
                )
            )

            self._logger.info(
                "Session %s | Run %s | Flow completed: %d steps",
                session_id,
                run_id,
                step_index,
            )

        except Exception as e:
            self._logger.error("Run %s failed: %s", run_id, e)
            asyncio.create_task(
                db_manager.update_flow_run_status(
                    run_id,
                    FlowRunStatus.FAILED,
                    error=str(e),
                )
            )
            raise

    async def run_async(
        self,
        session_id: Optional[str] = None,
        **kwargs: Any,
    ) -> str:
        """
        Run flow asynchronously with DB logging.

        Returns immediately with run_id. Flow executes in background.
        Poll GET /flows/{flow_id}/run/{run_id} for status.

        Args:
            session_id: Optional session ID for memory persistence
            **kwargs: Arguments passed to StartEvent

        Returns:
            run_id for polling
        """
        run_id = str(uuid.uuid4())

        self._logger.info(
            "Session %s | Run %s | Starting async flow: %s",
            session_id,
            run_id,
            kwargs,
        )

        # Fire-and-forget: run in background
        asyncio.create_task(
            self._execute_async_with_logging(run_id, session_id, **kwargs)
        )

        return run_id

    async def _execute_async_with_logging(
        self,
        run_id: str,
        session_id: Optional[str],
        **kwargs: Any,
    ) -> None:
        """Execute flow in background with DB logging."""
        try:
            # Consume all events (logging happens inside)
            async for _ in self.stream_flow_events_with_logging(
                run_id=run_id,
                session_id=session_id,
                **kwargs,
            ):
                pass  # Events are logged inside the generator
        except Exception as e:
            self._logger.error("Async run %s failed: %s", run_id, e)
            # Error is already logged in stream_flow_events_with_logging

    # ─────────────────────────────────────────────────────────────
    # EXECUTION METHODS
    # ─────────────────────────────────────────────────────────────

    async def execute(
        self,
        session_id: Optional[str] = None,
        **kwargs: Any,
    ) -> Any:
        """
        Run the flow with the given inputs.

        Args:
            session_id: Optional session ID for memory persistence
            **kwargs: Arguments passed to StartEvent

        Returns:
            The result from StopEvent
        """
        self._logger.info("Session %s | Starting flow with: %s", session_id, kwargs)

        # Store session_id in context for steps to access
        result = await self.run(**kwargs, _session_id=session_id)

        self._logger.info("Session %s | Flow completed: %s", session_id, result)
        return result

    async def stream_flow_events(
        self,
        session_id: Optional[str] = None,
        **kwargs: Any,
    ) -> AsyncGenerator[Any, None]:
        """
        Stream events from the flow execution.

        Args:
            session_id: Optional session ID for memory persistence
            **kwargs: Arguments passed to StartEvent

        Yields:
            Events emitted during flow execution
        """
        self._logger.info("Session %s | Streaming flow with: %s", session_id, kwargs)

        handler = self.run(**kwargs, _session_id=session_id)

        async for event in handler.stream_events():
            yield event

        # Get final result
        result = await handler
        self._logger.info("Session %s | Stream completed: %s", session_id, result)

    # ─────────────────────────────────────────────────────────────
    # HITL-AWARE METHODS
    # ─────────────────────────────────────────────────────────────

    async def run_with_hitl(
        self,
        session_id: Optional[str] = None,
        **kwargs: Any,
    ) -> FlowResult:
        """
        Run the flow with HITL support.

        Returns:
            - CompletedResult if flow finishes
            - HITLPendingResult if human input is required
        """
        self._logger.info("Session %s | HITL flow with: %s", session_id, kwargs)

        handler = self.run(**kwargs, _session_id=session_id)

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

        # Flow completed without HITL
        result = await handler
        self._logger.info("Session %s | Flow completed: %s", session_id, result)
        return CompletedResult(response=result)

    async def resume_with_input(
        self,
        context_dict: dict,
        human_response: str,
        user_name: str = "operator",
        session_id: Optional[str] = None,
    ) -> FlowResult:
        """
        Resume a paused flow with human input.

        Args:
            context_dict: Serialized context from HITLPendingResult
            human_response: The human's response
            user_name: Must match the user_name in InputRequiredEvent
            session_id: Session ID for restoring memory

        Returns:
            - CompletedResult if flow finishes
            - HITLPendingResult if another human input is required
        """
        self._logger.info("Resuming flow with response: %s", human_response)

        # Restore context
        ctx = Context.from_dict(self, context_dict)

        # Restore memory if needed
        memory = self._get_memory(session_id)
        if memory:
            await ctx.store.set("memory", memory)

        # Resume flow
        handler = self.run(ctx=ctx)

        # Send human response
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

        # Flow completed
        result = await handler
        self._logger.info("Resumed flow completed: %s", result)
        return CompletedResult(response=result)

    async def clear_session(self, session_id: str) -> bool:
        """Clear memory for a specific session."""
        cleared = await db_manager.clear_memory(session_id, self.NAME)
        self._logger.info("Cleared memory for session: %s", session_id)
        return cleared
