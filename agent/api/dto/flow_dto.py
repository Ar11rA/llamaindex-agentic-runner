"""
DTOs for Flow API endpoints.
"""

from typing import Optional, Any

from pydantic import BaseModel


class FlowRequest(BaseModel):
    """Request model for flow endpoints."""

    topic: str  # For story_flow
    session_id: Optional[str] = None


class FlowResponse(BaseModel):
    """Response model for completed flow."""

    status: str = "completed"
    result: Any
    session_id: Optional[str] = None
    run_id: Optional[str] = None  # For tracking in DB


class HITLPendingResponse(BaseModel):
    """Response when human input is required."""

    status: str = "pending_input"
    workflow_id: str
    prompt: str
    session_id: Optional[str] = None


class HITLRespondRequest(BaseModel):
    """Request model for providing human input."""

    workflow_id: str
    response: str


# ─────────────────────────────────────────────────────────────
# ASYNC FLOW DTOs
# ─────────────────────────────────────────────────────────────


class AsyncFlowResponse(BaseModel):
    """Response for async flow start - returns run_id for polling."""

    run_id: str
    status: str = "pending"


class FlowStepResponse(BaseModel):
    """Response model for a single flow step."""

    id: str
    step_name: str
    step_index: int
    status: str
    event_type: Optional[str] = None
    event_data: Optional[dict] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    duration_ms: Optional[int] = None


class FlowRunResponse(BaseModel):
    """Response model for flow run status (polling endpoint)."""

    run_id: str
    flow_id: str
    status: str
    input_data: Optional[dict] = None
    result: Optional[str] = None
    error: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    metadata: Optional[dict] = None
    steps: Optional[list[FlowStepResponse]] = None
