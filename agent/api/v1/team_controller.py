"""
API endpoints for multi-agent teams - listing and chat interactions.
"""

import asyncio
import json
import logging
import uuid

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from llama_index.core.workflow import Context, InputRequiredEvent, HumanResponseEvent
from llama_index.core.agent.workflow.workflow_events import AgentStream

from api.dto.team_dto import (
    ChatRequest,
    ChatResponse,
    HITLPendingResponse,
    HITLRespondRequest,
    StreamRespondRequest,
)
from config.database import db_manager, WorkflowStatus
from teams import team_registry, HITLPendingResult

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/teams", tags=["teams"])


# ─────────────────────────────────────────────────────────────
# LIST TEAMS
# ─────────────────────────────────────────────────────────────


@router.get("")
async def list_teams():
    """List all available multi-agent teams."""
    return {"teams": team_registry.list_teams()}


# ─────────────────────────────────────────────────────────────
# CHAT ENDPOINTS (JSON)
# ─────────────────────────────────────────────────────────────


@router.post("/{team_name}/chat")
async def chat(team_name: str, request: ChatRequest):
    """
    Send a message to a team (supports HITL).

    - If the team completes normally: returns ChatResponse
    - If HITL is triggered: returns HITLPendingResponse

    Use POST /{team_name}/chat/respond to provide human input when status is 'pending_input'.
    """
    team = team_registry.get(team_name)
    if team is None:
        raise HTTPException(
            status_code=404,
            detail=f"Team '{team_name}' not found. Use GET /api/v1/teams to list available teams.",
        )

    # Run with HITL support
    result = await team.run_with_hitl(request.message, session_id=request.session_id)

    if isinstance(result, HITLPendingResult):
        # Save workflow state to database
        await db_manager.save_workflow_state(
            workflow_id=result.workflow_id,
            agent_name=team_name,  # Store team name
            context_data=result.context_dict,
            prompt=result.prompt,
            session_id=request.session_id,
            user_name=result.user_name,
        )

        return HITLPendingResponse(
            workflow_id=result.workflow_id,
            prompt=result.prompt,
            active_agent=result.active_agent,
            session_id=request.session_id,
        )
    else:
        return ChatResponse(
            response=result.response,
            session_id=request.session_id,
            responding_agents=result.responding_agents,
        )


@router.post("/{team_name}/chat/respond")
async def respond_to_hitl(team_name: str, request: HITLRespondRequest):
    """
    Provide human input to resume a paused team (JSON response).

    - **workflow_id**: The workflow ID from the pending_input response
    - **response**: The human's response (e.g., "yes" or "no")

    Returns:
    - ChatResponse if team completes
    - HITLPendingResponse if another input is required
    """
    team = team_registry.get(team_name)
    if team is None:
        raise HTTPException(status_code=404, detail=f"Team '{team_name}' not found.")

    # Load workflow state from database
    state = await db_manager.get_workflow_state(request.workflow_id)

    if state is None:
        raise HTTPException(
            status_code=404,
            detail=f"Workflow state '{request.workflow_id}' not found.",
        )

    if state["status"] != WorkflowStatus.PENDING_INPUT.value:
        raise HTTPException(
            status_code=400,
            detail=f"Workflow '{request.workflow_id}' is not pending input (status: {state['status']}).",
        )

    if state["agent_name"] != team_name:
        raise HTTPException(
            status_code=400,
            detail=f"Workflow state '{request.workflow_id}' belongs to '{state['agent_name']}', not '{team_name}'.",
        )

    # Resume team with human input
    result = await team.resume_with_input(
        context_dict=state["context_data"],
        human_response=request.response,
        user_name=state.get("user_name", "operator"),
        session_id=state.get("session_id"),
    )

    if isinstance(result, HITLPendingResult):
        # Another HITL triggered - save new state
        await db_manager.save_workflow_state(
            workflow_id=result.workflow_id,
            agent_name=team_name,
            context_data=result.context_dict,
            prompt=result.prompt,
            session_id=state.get("session_id"),
            user_name=result.user_name,
        )

        # Mark old workflow state as completed
        await db_manager.update_workflow_status(
            request.workflow_id, WorkflowStatus.COMPLETED
        )

        return HITLPendingResponse(
            workflow_id=result.workflow_id,
            prompt=result.prompt,
            active_agent=result.active_agent,
            session_id=state.get("session_id"),
        )
    else:
        # Team completed - update status
        await db_manager.update_workflow_status(
            request.workflow_id, WorkflowStatus.COMPLETED
        )

        return ChatResponse(
            response=result.response,
            session_id=state.get("session_id"),
            responding_agents=result.responding_agents,
        )


@router.get("/{team_name}/chat/status/{workflow_id}")
async def get_workflow_status(team_name: str, workflow_id: str):
    """Get the status of a team workflow execution."""
    state = await db_manager.get_workflow_state(workflow_id)

    if state is None:
        raise HTTPException(
            status_code=404,
            detail=f"Workflow state '{workflow_id}' not found.",
        )

    return {
        "workflow_id": state["workflow_id"],
        "team_name": state["agent_name"],
        "status": state["status"],
        "prompt": state["prompt"],
        "session_id": state["session_id"],
        "created_at": state["created_at"].isoformat() if state["created_at"] else None,
        "updated_at": state["updated_at"].isoformat() if state["updated_at"] else None,
    }


# ─────────────────────────────────────────────────────────────
# STREAMING ENDPOINTS WITH HITL SUPPORT
# ─────────────────────────────────────────────────────────────


@router.post("/{team_name}/chat/stream")
async def chat_stream(team_name: str, request: ChatRequest):
    """
    Stream team response with HITL support and agent tracking.

    SSE Events:
    - `event: agent\\ndata: {"agent_name": "..."}` - Agent change notification
    - `data: <token>` - Regular stream tokens
    - `event: hitl\\ndata: {"workflow_id": "...", "prompt": "...", "active_agent": "..."}` - HITL required
    - `data: [HITL_PAUSE]` - Stream paused for human input
    - `data: [DONE]` - Stream complete

    When you receive an `hitl` event, use POST /{team_name}/chat/stream/respond to resume.
    """
    team = team_registry.get(team_name)
    if team is None:
        raise HTTPException(
            status_code=404,
            detail=f"Team '{team_name}' not found. Use GET /api/v1/teams to list available teams.",
        )

    async def event_generator():
        memory = team._get_memory(request.session_id)
        handler = team.workflow.run(user_msg=request.message, memory=memory)

        # Track agent changes for SSE events
        last_agent = None

        try:
            async for event in handler.stream_events():
                # Check for agent change and emit event
                try:
                    current_agent = await handler.ctx.store.get(
                        "current_agent_name", default=None
                    )
                    if current_agent and current_agent != last_agent:
                        agent_data = json.dumps({"agent_name": current_agent})
                        yield f"event: agent\ndata: {agent_data}\n\n"
                        last_agent = current_agent
                except Exception:
                    pass

                if isinstance(event, AgentStream):
                    # Regular token - stream it
                    yield f"data: {event.delta}\n\n"

                elif isinstance(event, InputRequiredEvent):
                    # HITL triggered - save state and notify client
                    ctx_dict = handler.ctx.to_dict()
                    workflow_id = str(uuid.uuid4())

                    # Get current agent
                    active_agent = last_agent

                    # Save workflow state to database
                    await db_manager.save_workflow_state(
                        workflow_id=workflow_id,
                        agent_name=team_name,
                        context_data=ctx_dict,
                        prompt=event.prefix,
                        session_id=request.session_id,
                        user_name=getattr(event, "user_name", "operator"),
                    )

                    # Emit HITL event (named SSE event)
                    hitl_data = json.dumps(
                        {
                            "workflow_id": workflow_id,
                            "prompt": event.prefix,
                            "active_agent": active_agent,
                            "session_id": request.session_id,
                        }
                    )
                    yield f"event: hitl\ndata: {hitl_data}\n\n"
                    yield "data: [HITL_PAUSE]\n\n"

                    # End stream - client should call /chat/stream/respond
                    return

            yield "data: [DONE]\n\n"

        except asyncio.CancelledError:
            # Client disconnected
            logger.info(
                "Client disconnected from team stream: team=%s, session=%s",
                team_name,
                request.session_id,
            )
            raise  # Re-raise to properly clean up the connection

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        },
    )


@router.post("/{team_name}/chat/stream/respond")
async def chat_stream_respond(team_name: str, request: StreamRespondRequest):
    """
    Resume a paused team stream with human input.

    Use this after receiving an `hitl` event from the stream endpoint.

    SSE Events:
    - `event: agent\\ndata: {"agent_name": "..."}` - Agent change notification
    - `data: <token>` - Regular stream tokens
    - `event: hitl\\ndata: {...}` - Another HITL required (chain continues)
    - `data: [HITL_PAUSE]` - Stream paused for human input
    - `data: [DONE]` - Stream complete
    """
    team = team_registry.get(team_name)
    if team is None:
        raise HTTPException(status_code=404, detail=f"Team '{team_name}' not found.")

    # Load workflow state from database
    state = await db_manager.get_workflow_state(request.workflow_id)

    if state is None:
        raise HTTPException(
            status_code=404,
            detail=f"Workflow state '{request.workflow_id}' not found.",
        )

    if state["status"] != WorkflowStatus.PENDING_INPUT.value:
        raise HTTPException(
            status_code=400,
            detail=f"Workflow is not pending input (status: {state['status']}).",
        )

    if state["agent_name"] != team_name:
        raise HTTPException(
            status_code=400,
            detail=f"Workflow belongs to '{state['agent_name']}', not '{team_name}'.",
        )

    async def event_generator():
        # Restore context from serialized state
        ctx = Context.from_dict(team.workflow, state["context_data"])

        # Restore memory (it's not serializable)
        memory = team._get_memory(state.get("session_id"))
        if memory:
            await ctx.store.set("memory", memory)

        # Resume workflow with restored context
        handler = team.workflow.run(ctx=ctx)

        # Send the human response event to the running workflow
        handler.ctx.send_event(
            HumanResponseEvent(
                response=request.response,
                user_name=state.get("user_name", "operator"),
            )
        )

        # Track agent changes
        last_agent = None

        try:
            async for event in handler.stream_events():
                # Check for agent change and emit event
                try:
                    current_agent = await handler.ctx.store.get(
                        "current_agent_name", default=None
                    )
                    if current_agent and current_agent != last_agent:
                        agent_data = json.dumps({"agent_name": current_agent})
                        yield f"event: agent\ndata: {agent_data}\n\n"
                        last_agent = current_agent
                except Exception:
                    pass

                if isinstance(event, AgentStream):
                    yield f"data: {event.delta}\n\n"

                elif isinstance(event, InputRequiredEvent):
                    # Another HITL triggered - save new state
                    ctx_dict = handler.ctx.to_dict()
                    new_workflow_id = str(uuid.uuid4())

                    # Use tracked agent
                    active_agent = last_agent

                    await db_manager.save_workflow_state(
                        workflow_id=new_workflow_id,
                        agent_name=team_name,
                        context_data=ctx_dict,
                        prompt=event.prefix,
                        session_id=state.get("session_id"),
                        user_name=getattr(event, "user_name", "operator"),
                    )

                    # Mark old workflow state as completed
                    await db_manager.update_workflow_status(
                        request.workflow_id, WorkflowStatus.COMPLETED
                    )

                    hitl_data = json.dumps(
                        {
                            "workflow_id": new_workflow_id,
                            "prompt": event.prefix,
                            "active_agent": active_agent,
                            "session_id": state.get("session_id"),
                        }
                    )
                    yield f"event: hitl\ndata: {hitl_data}\n\n"
                    yield "data: [HITL_PAUSE]\n\n"
                    return

            # Mark workflow as completed
            await db_manager.update_workflow_status(
                request.workflow_id, WorkflowStatus.COMPLETED
            )

            yield "data: [DONE]\n\n"

        except asyncio.CancelledError:
            # Client disconnected during resume
            logger.info(
                "Client disconnected from team stream/respond: team=%s, workflow=%s",
                team_name,
                request.workflow_id,
            )
            raise  # Re-raise to properly clean up

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


@router.delete("/{team_name}/session/{session_id}")
async def clear_session(team_name: str, session_id: str):
    """Clear the conversation history for a specific team session."""
    team = team_registry.get(team_name)
    if team is None:
        raise HTTPException(status_code=404, detail=f"Team '{team_name}' not found.")

    cleared = await team.clear_session(session_id)
    return {"cleared": cleared, "session_id": session_id, "team": team_name}
