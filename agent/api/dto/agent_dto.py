"""
DTOs for Agent API endpoints.
"""

from typing import Optional

from pydantic import BaseModel


class ChatRequest(BaseModel):
    """Request model for agent chat endpoints."""

    message: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    """Response model for completed agent chat."""

    status: str = "completed"
    response: str
    session_id: Optional[str] = None
    agent_name: Optional[str] = None  # The agent that responded


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


class StreamRespondRequest(BaseModel):
    """Request model for resuming a stream with human input."""

    workflow_id: str
    response: str
