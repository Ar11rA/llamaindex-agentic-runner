"""
DTOs for Team API endpoints.
"""

from typing import Optional, List

from pydantic import BaseModel


class ChatRequest(BaseModel):
    """Request model for team chat endpoints."""

    message: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    """Response model for completed team chat."""

    status: str = "completed"
    response: str
    session_id: Optional[str] = None
    responding_agents: Optional[List[str]] = None  # Agents that participated


class HITLPendingResponse(BaseModel):
    """Response when human input is required."""

    status: str = "pending_input"
    workflow_id: str
    prompt: str
    active_agent: Optional[str] = None  # Which agent triggered HITL
    session_id: Optional[str] = None


class HITLRespondRequest(BaseModel):
    """Request model for providing human input."""

    workflow_id: str
    response: str


class StreamRespondRequest(BaseModel):
    """Request model for resuming a stream with human input."""

    workflow_id: str
    response: str
