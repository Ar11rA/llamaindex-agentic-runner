from typing import List, Callable, Any

from agents.base import BaseAgent
from tools.market_tools import get_index, push_index


class MarketAgent(BaseAgent):
    """An agent that manages market index data with human-in-the-loop for dangerous operations."""

    NAME = "market"
    DESCRIPTION = (
        "An agent that can retrieve and update market index data. "
        "Dangerous operations like pushing/updating data require human confirmation."
    )
    DEFAULT_SYSTEM_PROMPT = (
        "You are a market data assistant. You have two tools:\n"
        "- get_index: Retrieve current market index values\n"
        "- push_index: Update/push market index values\n\n"
        "Available indices: SP500, NASDAQ, DOW, NIFTY, SENSEX.\n\n"
        "IMPORTANT: When the user asks to update an index, call push_index directly. "
        "Do NOT ask for confirmation yourself - the tool will handle any required "
        "confirmations automatically. Just call the tool."
    )

    def get_tools(self) -> List[Callable[..., Any]]:
        return [get_index, push_index]
