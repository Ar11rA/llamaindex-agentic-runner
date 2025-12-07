"""
API endpoints for single agents - listing and chat interactions.
"""

import asyncio
import json
import logging
import uuid

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from llama_index.core.workflow import Context, InputRequiredEvent, HumanResponseEvent
from llama_index.core.agent.workflow.workflow_events import AgentStream

from agents import registry, HITLPendingResult
from api.dto.agent_dto import (
    ChatRequest,
    ChatResponse,
    HITLPendingResponse,
    HITLRespondRequest,
    StreamRespondRequest,
)
from config.database import db_manager, WorkflowStatus

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agents", tags=["agents"])


# ─────────────────────────────────────────────────────────────
# LIST AGENTS
# ─────────────────────────────────────────────────────────────


@router.get("")
async def list_agents():
    """List all available agents."""
    return {"agents": registry.list_agents()}


# ─────────────────────────────────────────────────────────────
# CHAT ENDPOINTS (JSON)
# ─────────────────────────────────────────────────────────────


@router.post("/{agent_id}/chat")
async def chat(agent_id: str, request: ChatRequest):
    """
    Send a message to a specific agent (supports HITL).

    - If the agent completes normally: returns ChatResponse
    - If HITL is triggered: returns HITLPendingResponse

    Use POST /{agent_id}/chat/respond to provide human input when status is 'pending_input'.
    """
    agent = registry.get(agent_id)
    if agent is None:
        raise HTTPException(
            status_code=404,
            detail=f"Agent '{agent_id}' not found. Use GET /api/v1/agents to list available agents.",
        )

    # Run with HITL support
    result = await agent.run_with_hitl(request.message, session_id=request.session_id)

    if isinstance(result, HITLPendingResult):
        # Save workflow state to database
        await db_manager.save_workflow_state(
            workflow_id=result.workflow_id,
            agent_name=agent_id,
            context_data=result.context_dict,
            prompt=result.prompt,
            session_id=request.session_id,
            user_name=result.user_name,
        )

        return HITLPendingResponse(
            workflow_id=result.workflow_id,
            prompt=result.prompt,
            session_id=request.session_id,
        )
    else:
        return ChatResponse(
            response=result.response,
            session_id=request.session_id,
            agent_name=agent_id,
        )


@router.post("/{agent_id}/chat/respond")
async def respond_to_hitl(agent_id: str, request: HITLRespondRequest):
    """
    Provide human input to resume a paused workflow (JSON response).

    - **workflow_id**: The workflow ID from the pending_input response
    - **response**: The human's response (e.g., "yes" or "no")

    Returns:
    - ChatResponse if workflow completes
    - HITLPendingResponse if another input is required
    """
    agent = registry.get(agent_id)
    if agent is None:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found.")

    # Load workflow state from database
    state = await db_manager.get_workflow_state(request.workflow_id)

    if state is None:
        raise HTTPException(
            status_code=404,
            detail=f"Workflow '{request.workflow_id}' not found.",
        )

    if state["status"] != WorkflowStatus.PENDING_INPUT.value:
        raise HTTPException(
            status_code=400,
            detail=f"Workflow '{request.workflow_id}' is not pending input (status: {state['status']}).",
        )

    if state["agent_name"] != agent_id:
        raise HTTPException(
            status_code=400,
            detail=f"Workflow '{request.workflow_id}' belongs to agent '{state['agent_name']}', not '{agent_id}'.",
        )

    # Resume workflow with human input
    result = await agent.resume_with_input(
        context_dict=state["context_data"],
        human_response=request.response,
        user_name=state.get("user_name", "operator"),
        session_id=state.get("session_id"),
    )

    if isinstance(result, HITLPendingResult):
        # Another HITL triggered - update state
        await db_manager.save_workflow_state(
            workflow_id=result.workflow_id,
            agent_name=agent_id,
            context_data=result.context_dict,
            prompt=result.prompt,
            session_id=state.get("session_id"),
            user_name=result.user_name,
        )

        # Mark old workflow as completed (replaced by new one)
        await db_manager.update_workflow_status(
            request.workflow_id, WorkflowStatus.COMPLETED
        )

        return HITLPendingResponse(
            workflow_id=result.workflow_id,
            prompt=result.prompt,
            session_id=state.get("session_id"),
        )
    else:
        # Workflow completed - update status
        await db_manager.update_workflow_status(
            request.workflow_id, WorkflowStatus.COMPLETED
        )

        return ChatResponse(
            response=result.response,
            session_id=state.get("session_id"),
            agent_name=agent_id,
        )


@router.get("/{agent_id}/chat/status/{workflow_id}")
async def get_workflow_status(agent_id: str, workflow_id: str):
    """Get the status of a workflow."""
    state = await db_manager.get_workflow_state(workflow_id)

    if state is None:
        raise HTTPException(
            status_code=404,
            detail=f"Workflow '{workflow_id}' not found.",
        )

    return {
        "workflow_id": state["workflow_id"],
        "agent_name": state["agent_name"],
        "status": state["status"],
        "prompt": state["prompt"],
        "session_id": state["session_id"],
        "created_at": state["created_at"].isoformat() if state["created_at"] else None,
        "updated_at": state["updated_at"].isoformat() if state["updated_at"] else None,
    }


# ─────────────────────────────────────────────────────────────
# STREAMING ENDPOINTS WITH HITL SUPPORT
# ─────────────────────────────────────────────────────────────


@router.post("/{agent_id}/chat/stream")
async def chat_stream(agent_id: str, request: ChatRequest):
    """
    Stream agent response with HITL support and agent tracking.

    SSE Events:
    - `event: agent\\ndata: {"agent_name": "..."}` - Agent identification
    - `data: <token>` - Regular stream tokens
    - `event: hitl\\ndata: {"workflow_id": "...", "prompt": "..."}` - HITL required
    - `data: [HITL_PAUSE]` - Stream paused for human input
    - `data: [DONE]` - Stream complete

    When you receive an `hitl` event, use POST /{agent_id}/chat/stream/respond to resume.
    """
    agent = registry.get(agent_id)
    if agent is None:
        raise HTTPException(
            status_code=404,
            detail=f"Agent '{agent_id}' not found. Use GET /api/v1/agents to list available agents.",
        )

    async def event_generator():
        # Emit agent identification at start
        agent_data = json.dumps({"agent_name": agent_id})
        yield f"event: agent\ndata: {agent_data}\n\n"

        memory = agent._get_memory(request.session_id)
        handler = agent.agent.run(user_msg=request.message, memory=memory)

        try:
            async for event in handler.stream_events():
                if isinstance(event, AgentStream):
                    # Regular token - stream it
                    yield f"data: {event.delta}\n\n"

                elif isinstance(event, InputRequiredEvent):
                    # HITL triggered - save state and notify client
                    ctx_dict = handler.ctx.to_dict()
                    workflow_id = str(uuid.uuid4())

                    # Save workflow state to database
                    await db_manager.save_workflow_state(
                        workflow_id=workflow_id,
                        agent_name=agent_id,
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
                            "agent_name": agent_id,
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
                "Client disconnected from agent stream: agent=%s, session=%s",
                agent_id,
                request.session_id,
            )
            raise  # Re-raise to properly clean up

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        },
    )


@router.post("/{agent_id}/chat/stream/respond")
async def chat_stream_respond(agent_id: str, request: StreamRespondRequest):
    """
    Resume a paused agent stream with human input.

    Use this after receiving an `hitl` event from the stream endpoint.

    SSE Events:
    - `event: agent\\ndata: {"agent_name": "..."}` - Agent identification
    - `data: <token>` - Regular stream tokens
    - `event: hitl\\ndata: {...}` - Another HITL required (chain continues)
    - `data: [HITL_PAUSE]` - Stream paused for human input
    - `data: [DONE]` - Stream complete
    """
    agent = registry.get(agent_id)
    if agent is None:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found.")

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

    if state["agent_name"] != agent_id:
        raise HTTPException(
            status_code=400,
            detail=f"Workflow belongs to agent '{state['agent_name']}', not '{agent_id}'.",
        )

    async def event_generator():
        # Emit agent identification at start
        agent_data = json.dumps({"agent_name": agent_id})
        yield f"event: agent\ndata: {agent_data}\n\n"

        # Restore context from serialized state
        ctx = Context.from_dict(agent.agent, state["context_data"])

        # Restore memory (it's not serializable)
        memory = agent._get_memory(state.get("session_id"))
        if memory:
            await ctx.store.set("memory", memory)

        # Resume workflow with restored context
        handler = agent.agent.run(ctx=ctx)

        # Send the human response event to the running workflow
        handler.ctx.send_event(
            HumanResponseEvent(
                response=request.response,
                user_name=state.get("user_name", "operator"),
            )
        )

        try:
            async for event in handler.stream_events():
                if isinstance(event, AgentStream):
                    yield f"data: {event.delta}\n\n"

                elif isinstance(event, InputRequiredEvent):
                    # Another HITL triggered - save new state
                    ctx_dict = handler.ctx.to_dict()
                    new_workflow_id = str(uuid.uuid4())

                    await db_manager.save_workflow_state(
                        workflow_id=new_workflow_id,
                        agent_name=agent_id,
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
                            "agent_name": agent_id,
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
                "Client disconnected from agent stream/respond: agent=%s, workflow=%s",
                agent_id,
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


@router.delete("/{agent_id}/session/{session_id}")
async def clear_session(agent_id: str, session_id: str):
    """Clear the conversation history for a specific session."""
    agent = registry.get(agent_id)
    if agent is None:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found.")

    cleared = await agent.clear_session(session_id)
    return {"cleared": cleared, "session_id": session_id}
