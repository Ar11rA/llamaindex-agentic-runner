"""
Data Transfer Objects (DTOs) for API request/response models.
"""

from api.dto.agent_dto import (
    ChatRequest as AgentChatRequest,
    ChatResponse as AgentChatResponse,
    HITLPendingResponse as AgentHITLPendingResponse,
    HITLRespondRequest as AgentHITLRespondRequest,
    StreamRespondRequest as AgentStreamRespondRequest,
)

from api.dto.team_dto import (
    ChatRequest as TeamChatRequest,
    ChatResponse as TeamChatResponse,
    HITLPendingResponse as TeamHITLPendingResponse,
    HITLRespondRequest as TeamHITLRespondRequest,
    StreamRespondRequest as TeamStreamRespondRequest,
)

from api.dto.flow_dto import (
    FlowRequest,
    FlowResponse,
    HITLPendingResponse as FlowHITLPendingResponse,
    HITLRespondRequest as FlowHITLRespondRequest,
)

__all__ = [
    # Agent DTOs
    "AgentChatRequest",
    "AgentChatResponse",
    "AgentHITLPendingResponse",
    "AgentHITLRespondRequest",
    "AgentStreamRespondRequest",
    # Team DTOs
    "TeamChatRequest",
    "TeamChatResponse",
    "TeamHITLPendingResponse",
    "TeamHITLRespondRequest",
    "TeamStreamRespondRequest",
    # Flow DTOs
    "FlowRequest",
    "FlowResponse",
    "FlowHITLPendingResponse",
    "FlowHITLRespondRequest",
]
