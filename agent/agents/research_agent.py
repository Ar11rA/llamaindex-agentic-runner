from typing import List, Callable, Any

from agents.base import BaseAgent
from tools.research_tools import web_search


class ResearchAgent(BaseAgent):
    """An agent that searches the web for information."""

    NAME = "research"
    DESCRIPTION = (
        "An agent that can search the web for information using Perplexity AI."
    )
    DEFAULT_SYSTEM_PROMPT = (
        "You are a research assistant that can search the web for information. "
        "Use your web search tool to find accurate and up-to-date information "
        "to answer user questions."
    )

    def get_tools(self) -> List[Callable[..., Any]]:
        return [web_search]
