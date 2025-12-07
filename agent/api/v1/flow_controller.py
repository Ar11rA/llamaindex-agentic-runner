"""
API endpoints for event-driven flows.
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from api.dto.flow_dto import (
    AsyncFlowResponse,
    FlowRequest,
    FlowResponse,
    FlowRunResponse,
    FlowStepResponse,
    HITLPendingResponse,
    HITLRespondRequest,
)
from config.database import FlowRunStatus, WorkflowStatus, db_manager
from flows import HITLPendingResult, flow_registry

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/flows", tags=["flows"])


# ─────────────────────────────────────────────────────────────
# LIST FLOWS
# ─────────────────────────────────────────────────────────────


@router.get("")
async def list_flows():
    """List all available flows."""
    return {"flows": flow_registry.list_flows()}


# ─────────────────────────────────────────────────────────────
# EXECUTE FLOW
# ─────────────────────────────────────────────────────────────


@router.post("/{flow_id}/run")
async def run_flow(flow_id: str, request: FlowRequest):
    """
    Run a flow synchronously with DB logging (supports HITL).

    Returns:
    - FlowResponse if flow completes (includes run_id for reference)
    - HITLPendingResponse if human input required
    """
    flow = flow_registry.get(flow_id)
    if flow is None:
        raise HTTPException(
            status_code=404,
            detail=f"Flow '{flow_id}' not found. Use GET /api/v1/flows to list available flows.",
        )

    run_id = str(uuid.uuid4())
    final_result = None

    # Use logging wrapper - consumes all events and logs to DB
    async for _run_id, event in flow.stream_flow_events_with_logging(
        run_id=run_id,
        topic=request.topic,
        session_id=request.session_id,
    ):
        # Check for HITL
        if isinstance(event, HITLPendingResult):
            await db_manager.save_workflow_state(
                workflow_id=event.workflow_id,
                agent_name=flow_id,
                context_data=event.context_dict,
                prompt=event.prompt,
                session_id=request.session_id,
                user_name=event.user_name,
            )

            return HITLPendingResponse(
                workflow_id=event.workflow_id,
                prompt=event.prompt,
                session_id=request.session_id,
            )

        # Capture final result from StopEvent
        event_type = type(event).__name__
        if event_type == "StopEvent" and hasattr(event, "result"):
            final_result = event.result

    return FlowResponse(
        result=final_result,
        session_id=request.session_id,
        run_id=run_id,
    )


@router.post("/{flow_id}/run/respond")
async def respond_to_hitl(flow_id: str, request: HITLRespondRequest):
    """Provide human input to resume a paused flow."""
    flow = flow_registry.get(flow_id)
    if flow is None:
        raise HTTPException(status_code=404, detail=f"Flow '{flow_id}' not found.")

    state = await db_manager.get_workflow_state(request.workflow_id)
    if state is None:
        raise HTTPException(
            status_code=404,
            detail=f"Workflow state '{request.workflow_id}' not found.",
        )

    result = await flow.resume_with_input(
        context_dict=state["context_data"],
        human_response=request.response,
        user_name=state.get("user_name", "operator"),
        session_id=state.get("session_id"),
    )

    await db_manager.update_workflow_status(
        request.workflow_id, WorkflowStatus.COMPLETED
    )

    if isinstance(result, HITLPendingResult):
        await db_manager.save_workflow_state(
            workflow_id=result.workflow_id,
            agent_name=flow_id,
            context_data=result.context_dict,
            prompt=result.prompt,
            session_id=state.get("session_id"),
            user_name=result.user_name,
        )

        return HITLPendingResponse(
            workflow_id=result.workflow_id,
            prompt=result.prompt,
            session_id=state.get("session_id"),
        )
    else:
        return FlowResponse(
            result=result.response,
            session_id=state.get("session_id"),
        )


# ─────────────────────────────────────────────────────────────
# ASYNC EXECUTION (Polling-based alternative to SSE)
# ─────────────────────────────────────────────────────────────


@router.post("/{flow_id}/run/async")
async def run_flow_async(flow_id: str, request: FlowRequest) -> AsyncFlowResponse:
    """
    Start a flow asynchronously.

    Returns immediately with a run_id. Poll GET /{flow_id}/run/{run_id} for status.
    This is an alternative to SSE streaming for long-running flows.
    """
    flow = flow_registry.get(flow_id)
    if flow is None:
        raise HTTPException(
            status_code=404,
            detail=f"Flow '{flow_id}' not found. Use GET /api/v1/flows to list available flows.",
        )

    run_id = await flow.run_async(
        topic=request.topic,
        session_id=request.session_id,
    )

    return AsyncFlowResponse(run_id=run_id, status="pending")


@router.get("/{flow_id}/run/{run_id}")
async def poll_flow_run(
    flow_id: str, run_id: str, include_steps: bool = False
) -> FlowRunResponse:
    """
    Poll the status of a flow run.

    Args:
        flow_id: The flow identifier
        run_id: The run ID returned from POST /run/async
        include_steps: If true, include step details in response

    Returns:
        FlowRunResponse with current status, result (if completed), or error (if failed)
    """
    run = await db_manager.get_flow_run(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found.")

    if run["flow_id"] != flow_id:
        raise HTTPException(
            status_code=404,
            detail=f"Run '{run_id}' not found for flow '{flow_id}'.",
        )

    steps = None
    if include_steps:
        step_rows = await db_manager.get_flow_steps(run_id)
        steps = [
            FlowStepResponse(
                id=s["id"],
                step_name=s["step_name"],
                step_index=s["step_index"],
                status=s["status"],
                event_type=s.get("event_type"),
                event_data=s.get("event_data"),
                started_at=s["started_at"].isoformat() if s.get("started_at") else None,
                completed_at=s["completed_at"].isoformat()
                if s.get("completed_at")
                else None,
                duration_ms=s.get("duration_ms"),
            )
            for s in step_rows
        ]

    return FlowRunResponse(
        run_id=run["id"],
        flow_id=run["flow_id"],
        status=run["status"],
        input_data=run.get("input_data"),
        result=run.get("result"),
        error=run.get("error"),
        started_at=run["started_at"].isoformat() if run.get("started_at") else None,
        completed_at=run["completed_at"].isoformat()
        if run.get("completed_at")
        else None,
        metadata=run.get("metadata"),
        steps=steps,
    )


@router.get("/{flow_id}/run/{run_id}/steps")
async def get_flow_run_steps(flow_id: str, run_id: str) -> list[FlowStepResponse]:
    """
    Get all steps for a flow run.

    Returns detailed step information for progress tracking.
    """
    run = await db_manager.get_flow_run(run_id)
    if run is None or run["flow_id"] != flow_id:
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found.")

    step_rows = await db_manager.get_flow_steps(run_id)
    return [
        FlowStepResponse(
            id=s["id"],
            step_name=s["step_name"],
            step_index=s["step_index"],
            status=s["status"],
            event_type=s.get("event_type"),
            event_data=s.get("event_data"),
            started_at=s["started_at"].isoformat() if s.get("started_at") else None,
            completed_at=s["completed_at"].isoformat()
            if s.get("completed_at")
            else None,
            duration_ms=s.get("duration_ms"),
        )
        for s in step_rows
    ]


# ─────────────────────────────────────────────────────────────
# STREAMING
# ─────────────────────────────────────────────────────────────


def _serialize_event(event: Any, max_str_len: int = 500) -> dict:
    """
    Generically serialize any Pydantic Event to a dict.

    - Includes all public attributes
    - Truncates long strings
    - Adds length for long content
    """
    event_data = {"type": type(event).__name__}

    # Get all fields from the event (Pydantic models have model_fields)
    if hasattr(event, "model_fields"):
        for field_name in event.model_fields:
            value = getattr(event, field_name, None)

            if value is None:
                event_data[field_name] = None
            elif isinstance(value, str):
                # Truncate long strings, add length
                if len(value) > max_str_len:
                    event_data[field_name] = value[:max_str_len] + "..."
                    event_data[f"{field_name}_length"] = len(value)
                else:
                    event_data[field_name] = value
            elif isinstance(value, (int, float, bool)):
                event_data[field_name] = value
            elif isinstance(value, dict):
                event_data[field_name] = value
            elif isinstance(value, list):
                event_data[field_name] = value[:10]  # Limit list items
                if len(value) > 10:
                    event_data[f"{field_name}_count"] = len(value)
            else:
                # Fallback: convert to string
                event_data[field_name] = str(value)

    # Handle result attribute specially (common in StopEvent)
    if hasattr(event, "result"):
        result = event.result
        if isinstance(result, dict):
            event_data["result"] = result
        elif isinstance(result, str) and len(result) > max_str_len:
            event_data["result"] = result[:max_str_len] + "..."
            event_data["result_length"] = len(result)
        else:
            event_data["result"] = result

    return event_data


@router.post("/{flow_id}/stream")
async def stream_flow(flow_id: str, request: FlowRequest):
    """
    Stream flow execution events with rich metadata and DB logging.

    SSE Events emitted (generic, based on flow events):
    - Each event type from the flow (e.g., ResearchCompleteEvent, ArticleWrittenEvent)
    - `done` - Final event with total steps, time, and run_id for reference

    Handles client disconnection gracefully by marking the flow as cancelled.
    """
    flow = flow_registry.get(flow_id)
    if flow is None:
        raise HTTPException(status_code=404, detail=f"Flow '{flow_id}' not found.")

    async def event_generator():
        started_at = datetime.utcnow()
        step_count = 0
        run_id = None

        try:
            # Use logging wrapper - logs to DB while streaming
            async for _run_id, event in flow.stream_flow_events_with_logging(
                topic=request.topic,
                session_id=request.session_id,
            ):
                run_id = _run_id
                step_count += 1

                # Generically serialize the event
                event_data = _serialize_event(event)

                # Add metadata
                event_data["_step"] = step_count
                event_data["_run_id"] = run_id
                event_data["_elapsed_ms"] = int(
                    (datetime.utcnow() - started_at).total_seconds() * 1000
                )
                event_data["_timestamp"] = datetime.utcnow().isoformat()

                yield f"event: {event_data['type']}\ndata: {json.dumps(event_data)}\n\n"

            # Done event - includes run_id for future reference
            done_data = {
                "_run_id": run_id,
                "_total_steps": step_count,
                "_total_ms": int(
                    (datetime.utcnow() - started_at).total_seconds() * 1000
                ),
            }
            yield f"event: done\ndata: {json.dumps(done_data)}\n\n"

        except asyncio.CancelledError:
            # Client disconnected - mark flow as cancelled
            logger.info("Client disconnected, cancelling flow run: %s", run_id)
            if run_id:
                await db_manager.update_flow_run_status(
                    run_id,
                    FlowRunStatus.CANCELLED,
                    metadata={
                        "cancelled_at_step": step_count,
                        "cancelled_at": datetime.utcnow().isoformat(),
                    },
                )
            raise  # Re-raise to properly clean up the connection

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# ─────────────────────────────────────────────────────────────
# SESSION MANAGEMENT
# ─────────────────────────────────────────────────────────────


@router.delete("/{flow_id}/session/{session_id}")
async def clear_session(flow_id: str, session_id: str):
    """Clear session memory for a flow."""
    flow = flow_registry.get(flow_id)
    if flow is None:
        raise HTTPException(status_code=404, detail=f"Flow '{flow_id}' not found.")

    cleared = await flow.clear_session(session_id)
    return {"cleared": cleared, "session_id": session_id, "flow": flow_id}
