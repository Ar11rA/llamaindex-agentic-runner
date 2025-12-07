"""
Event-driven workflow (Flow) registry and exports.

Flows are different from Teams:
- Teams: Multi-agent orchestration using AgentWorkflow (handoffs or orchestrator pattern)
- Flows: Event-driven pipelines using LlamaIndex Workflow (@step decorator, custom Events)
"""

from typing import Protocol, runtime_checkable, Any

from flows.base import (
    BaseFlow,
    HITLPendingResult,
    CompletedResult,
    FlowResult,
)
from flows.story_flow import StoryFlow
from flows.story_critic_flow import StoryCriticFlow


@runtime_checkable
class FlowProtocol(Protocol):
    """Protocol defining the interface for flows."""

    NAME: str
    DESCRIPTION: str

    async def execute(self, session_id: str | None = None, **kwargs: Any) -> Any: ...

    async def run_with_hitl(
        self, session_id: str | None = None, **kwargs: Any
    ) -> FlowResult: ...

    async def resume_with_input(
        self,
        context_dict: dict,
        human_response: str,
        user_name: str = "operator",
        session_id: str | None = None,
    ) -> FlowResult: ...

    async def clear_session(self, session_id: str) -> bool: ...


class FlowRegistry:
    """Registry for managing available flows."""

    def __init__(self):
        self._flows: dict[str, FlowProtocol] = {}

    def register(self, flow_cls: type) -> None:
        """Register a flow class (instantiates it)."""
        instance = flow_cls()
        self._flows[instance.NAME] = instance

    def get(self, flow_id: str) -> FlowProtocol | None:
        """Get a flow by ID."""
        return self._flows.get(flow_id)

    def list_flows(self) -> list[dict]:
        """List all registered flows."""
        return [
            {
                "id": flow.NAME,
                "name": flow.NAME.replace("_", " ").title(),
                "description": flow.DESCRIPTION,
            }
            for flow in self._flows.values()
        ]


# Global flow registry
flow_registry = FlowRegistry()

# Register flows
flow_registry.register(StoryFlow)
flow_registry.register(StoryCriticFlow)

__all__ = [
    "BaseFlow",
    "HITLPendingResult",
    "CompletedResult",
    "FlowResult",
    "FlowProtocol",
    "FlowRegistry",
    "flow_registry",
    "StoryFlow",
    "StoryCriticFlow",
]
