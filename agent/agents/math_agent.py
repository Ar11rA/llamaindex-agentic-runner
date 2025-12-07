from typing import List, Callable, Any

from agents.base import BaseAgent
from tools.math_tools import multiply, add


class MathAgent(BaseAgent):
    """An agent that performs basic mathematical operations."""

    NAME = "math"
    DESCRIPTION = "An agent that can perform basic mathematical operations using tools."
    DEFAULT_SYSTEM_PROMPT = (
        "You are an agent that can perform basic mathematical operations using tools."
    )

    def get_tools(self) -> List[Callable[..., Any]]:
        return [multiply, add]
