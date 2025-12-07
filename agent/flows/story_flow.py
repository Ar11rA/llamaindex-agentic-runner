"""
Story Flow - Research a topic and write a news article.

Flow:
1. User provides a topic
2. Research agent gathers information
3. Writer agent crafts the article
4. Return the final article
"""

from llama_index.core.workflow import StartEvent, StopEvent, step, Context, Event

from flows.base import BaseFlow
from agents import ResearchAgent, WriterAgent


# ─────────────────────────────────────────────────────────────
# FLOW EVENTS
# ─────────────────────────────────────────────────────────────


class StepStartedEvent(Event):
    """Emitted when a step begins execution."""

    step_name: str
    details: str = ""


class StepCompleteEvent(Event):
    """Emitted when a step completes execution."""

    step_name: str
    status: str = "completed"
    data: dict = {}  # Flexible payload for step-specific data


# Internal routing events (not emitted to stream)
class ResearchCompleteEvent(Event):
    """Internal: Routes research results to write step."""

    topic: str
    research: str


# ─────────────────────────────────────────────────────────────
# STORY FLOW
# ─────────────────────────────────────────────────────────────


class StoryFlow(BaseFlow):
    """
    A flow that researches a topic and writes a news article.

    Steps:
    1. research: Takes user topic, calls ResearchAgent
    2. write: Takes research, calls WriterAgent
    3. Returns the final article
    """

    NAME = "story_flow"
    DESCRIPTION = (
        "A flow that researches a topic using web search and then writes "
        "a professional news article based on the research findings."
    )

    def __init__(self, timeout: float = 600.0, verbose: bool = False):
        super().__init__(timeout=timeout, verbose=verbose)

        # Initialize agents
        self._research_agent = ResearchAgent()
        self._writer_agent = WriterAgent()

        self._logger.info("StoryFlow initialized with ResearchAgent and WriterAgent")

    @step
    async def research(self, ctx: Context, ev: StartEvent) -> ResearchCompleteEvent:
        """
        Step 1: Research the topic using ResearchAgent.

        Receives: StartEvent with 'topic' attribute
        Emits: ResearchCompleteEvent with research findings
        """
        topic = ev.topic
        session_id = getattr(ev, "_session_id", None)

        # Emit step started event immediately
        ctx.write_event_to_stream(
            StepStartedEvent(step_name="research", details=f"Researching: {topic}")
        )

        self._logger.info("Researching topic: %s (session_id=%s)", topic, session_id)

        # Store session_id in context for later steps
        if session_id:
            await ctx.store.set("session_id", session_id)

        # Build research query
        research_query = (
            f"Research the following topic thoroughly for a news article: {topic}\n\n"
            "Gather key facts, recent developments, expert opinions, statistics, "
            "and any relevant context. Focus on accuracy and newsworthiness."
        )

        # Run research agent
        research_result = await self._research_agent.run(
            research_query, session_id=session_id
        )

        self._logger.info("Research complete: %d chars", len(research_result))

        # Emit generic event to stream for API consumers
        ctx.write_event_to_stream(
            StepCompleteEvent(
                step_name="research",
                data={"topic": topic, "research_length": len(research_result)},
            )
        )

        # Return typed event for internal workflow routing
        return ResearchCompleteEvent(topic=topic, research=research_result)

    @step
    async def write(self, ctx: Context, ev: ResearchCompleteEvent) -> StopEvent:
        """
        Step 2: Write the article using WriterAgent.

        Receives: ResearchCompleteEvent with research findings
        Emits: StopEvent with the final article
        """
        # Emit step started event immediately
        ctx.write_event_to_stream(
            StepStartedEvent(
                step_name="write", details=f"Writing article for: {ev.topic}"
            )
        )

        # Get session_id from context if available
        session_id = await ctx.store.get("session_id", default=None)

        self._logger.info(
            "Writing article for topic: %s (session_id=%s)", ev.topic, session_id
        )

        # Build writing prompt with research
        writing_prompt = f"""Write a professional news article about: {ev.topic}

## Research Notes
{ev.research}

## Instructions
Based on the research above, write a compelling news article that:
1. Has an attention-grabbing headline
2. Opens with the most newsworthy angle
3. Incorporates the key facts and findings
4. Provides context and background
5. Ends with a memorable conclusion

Write the complete article now."""

        # Run writer agent
        article = await self._writer_agent.run(writing_prompt, session_id=session_id)

        self._logger.info("Article complete: %d chars", len(article))

        # Emit generic event to stream for API consumers
        ctx.write_event_to_stream(
            StepCompleteEvent(
                step_name="write",
                data={"topic": ev.topic, "article_length": len(article)},
            )
        )

        # Return StopEvent with the final result
        return StopEvent(result=article)
