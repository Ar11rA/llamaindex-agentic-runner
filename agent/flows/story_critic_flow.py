"""
Story Critic Flow - Research, write, critique, and iterate.

Flow with branching/looping:
1. Research the topic
2. Write an article
3. Critic evaluates against guidelines
4. If approved → return to user
5. If rejected → send feedback to writer, retry (max 3 times)

Based on: https://developers.llamaindex.ai/python/llamaagents/workflows/branches_and_loops/
"""

import json
from llama_index.core.workflow import StartEvent, StopEvent, step, Context, Event

from flows.base import BaseFlow
from agents import ResearchAgent, WriterAgent, CriticAgent


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


# ─────────────────────────────────────────────────────────────
# INTERNAL ROUTING EVENTS (not emitted to stream)
# ─────────────────────────────────────────────────────────────


class ResearchCompleteEvent(Event):
    """Internal: Routes research results to write step."""

    topic: str
    research: str


class ArticleWrittenEvent(Event):
    """Internal: Routes article to critique step."""

    topic: str
    research: str
    article: str
    attempt: int


class CriticFeedbackEvent(Event):
    """Internal: Routes feedback back to rewrite step (loop)."""

    topic: str
    research: str
    article: str
    feedback: str
    attempt: int


# ─────────────────────────────────────────────────────────────
# STORY CRITIC FLOW
# ─────────────────────────────────────────────────────────────


class StoryCriticFlow(BaseFlow):
    """
    A flow that researches, writes, critiques, and iterates on articles.

    Implements branching/looping:
    - If critic approves → StopEvent (return article)
    - If critic rejects → CriticFeedbackEvent → rewrite (max 3 attempts)
    """

    NAME = "story_critic_flow"
    DESCRIPTION = (
        "A flow that researches a topic, writes an article, and iteratively "
        "improves it based on critic feedback until it meets editorial guidelines. "
        "Maximum 3 revision attempts."
    )
    MAX_ATTEMPTS = 3

    def __init__(self, timeout: float = 900.0, verbose: bool = False):
        super().__init__(timeout=timeout, verbose=verbose)

        # Initialize agents
        self._research_agent = ResearchAgent()
        self._writer_agent = WriterAgent()
        self._critic_agent = CriticAgent()

        self._logger.info(
            "StoryCriticFlow initialized with ResearchAgent, WriterAgent, CriticAgent"
        )

    @step
    async def research(self, ctx: Context, ev: StartEvent) -> ResearchCompleteEvent:
        """Step 1: Research the topic."""
        topic = ev.topic
        session_id = getattr(ev, "_session_id", None)

        # Emit step started event immediately
        ctx.write_event_to_stream(
            StepStartedEvent(step_name="research", details=f"Researching: {topic}")
        )

        self._logger.info("Researching topic: %s (session_id=%s)", topic, session_id)

        if session_id:
            await ctx.store.set("session_id", session_id)

        research_query = (
            f"Research the following topic thoroughly for a news article: {topic}\n\n"
            "Gather key facts, recent developments, expert opinions, statistics, "
            "and any relevant context. Focus on accuracy and newsworthiness."
        )

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
    async def write(
        self, ctx: Context, ev: ResearchCompleteEvent
    ) -> ArticleWrittenEvent:
        """Step 2: Write the initial article."""
        # Emit step started event immediately
        ctx.write_event_to_stream(
            StepStartedEvent(step_name="write", details="Writing initial article")
        )

        session_id = await ctx.store.get("session_id", default=None)

        self._logger.info("Writing initial article for: %s", ev.topic)

        writing_prompt = f"""Write a professional news article about: {ev.topic}

## Research Notes
{ev.research}

## Guidelines (MUST follow)
- Keep the article under 500 words
- Only use facts from the research notes above - do NOT fabricate
- Include a compelling headline
- Structure: headline, lede, body, conclusion
- Be objective and balanced

Write the complete article now."""

        article = await self._writer_agent.run(writing_prompt, session_id=session_id)

        self._logger.info("Initial article written: %d chars", len(article))

        # Emit generic event to stream for API consumers
        ctx.write_event_to_stream(
            StepCompleteEvent(
                step_name="write",
                data={"topic": ev.topic, "article_length": len(article), "attempt": 1},
            )
        )

        # Return typed event for internal workflow routing
        return ArticleWrittenEvent(
            topic=ev.topic,
            research=ev.research,
            article=article,
            attempt=1,
        )

    @step
    async def rewrite(
        self, ctx: Context, ev: CriticFeedbackEvent
    ) -> ArticleWrittenEvent:
        """Step 2b: Rewrite article based on critic feedback (loop)."""
        # Emit step started event immediately
        ctx.write_event_to_stream(
            StepStartedEvent(
                step_name="rewrite",
                details=f"Rewriting article (attempt {ev.attempt + 1})",
            )
        )

        session_id = await ctx.store.get("session_id", default=None)

        self._logger.info(
            "Rewriting article (attempt %d) based on feedback", ev.attempt + 1
        )

        rewrite_prompt = f"""Rewrite this news article based on the editor's feedback.

## Original Topic
{ev.topic}

## Research Notes (use ONLY these facts)
{ev.research}

## Current Article
{ev.article}

## Editor Feedback (MUST address)
{ev.feedback}

## Guidelines (MUST follow)
- Keep the article under 500 words
- Only use facts from the research notes - do NOT fabricate
- Include a compelling headline
- Structure: headline, lede, body, conclusion
- Be objective and balanced

Write the improved article now."""

        article = await self._writer_agent.run(rewrite_prompt, session_id=session_id)

        self._logger.info("Article rewritten: %d chars", len(article))

        # Emit generic event to stream for API consumers
        ctx.write_event_to_stream(
            StepCompleteEvent(
                step_name="rewrite",
                data={
                    "topic": ev.topic,
                    "article_length": len(article),
                    "attempt": ev.attempt + 1,
                },
            )
        )

        # Return typed event for internal workflow routing
        return ArticleWrittenEvent(
            topic=ev.topic,
            research=ev.research,
            article=article,
            attempt=ev.attempt + 1,
        )

    @step
    async def critique(
        self, ctx: Context, ev: ArticleWrittenEvent
    ) -> StopEvent | CriticFeedbackEvent:
        """
        Step 3: Critic evaluates the article.

        Branching logic:
        - If approved OR max attempts reached → StopEvent
        - If rejected AND attempts remaining → CriticFeedbackEvent (loop back)
        """
        # Emit step started event immediately
        ctx.write_event_to_stream(
            StepStartedEvent(
                step_name="critique",
                details=f"Critiquing article (attempt {ev.attempt}/{self.MAX_ATTEMPTS})",
            )
        )

        session_id = await ctx.store.get("session_id", default=None)

        self._logger.info(
            "Critiquing article (attempt %d/%d)", ev.attempt, self.MAX_ATTEMPTS
        )

        critique_prompt = f"""Review this article against our editorial guidelines.

## Research Notes (article should only use facts from here)
{ev.research}

## Article to Review
{ev.article}

Evaluate and respond with JSON: {{"approved": bool, "score": 1-10, "issues": [...], "feedback": "..."}}"""

        critique_result = await self._critic_agent.run(
            critique_prompt, session_id=session_id
        )

        self._logger.info("Critique result: %s", critique_result[:200])

        # Parse critic response
        try:
            # Extract JSON from response
            json_start = critique_result.find("{")
            json_end = critique_result.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                critique_json = json.loads(critique_result[json_start:json_end])
            else:
                critique_json = {"approved": False, "feedback": critique_result}
        except json.JSONDecodeError:
            critique_json = {"approved": False, "feedback": critique_result}

        approved = critique_json.get("approved", False)
        feedback = critique_json.get("feedback", "No specific feedback provided")
        score = critique_json.get("score", 0)

        self._logger.info(
            "Critique: approved=%s, score=%s, attempt=%d/%d",
            approved,
            score,
            ev.attempt,
            self.MAX_ATTEMPTS,
        )

        # Branching decision
        if approved:
            self._logger.info("Article APPROVED after %d attempt(s)", ev.attempt)

            # Emit generic event to stream
            ctx.write_event_to_stream(
                StepCompleteEvent(
                    step_name="critique",
                    status="approved",
                    data={
                        "attempt": ev.attempt,
                        "approved": True,
                        "score": score,
                    },
                )
            )

            return StopEvent(
                result={
                    "article": ev.article,
                    "attempts": ev.attempt,
                    "approved": True,
                    "score": score,
                }
            )

        if ev.attempt >= self.MAX_ATTEMPTS:
            self._logger.warning(
                "Max attempts reached (%d). Returning best effort.", self.MAX_ATTEMPTS
            )

            # Emit generic event to stream
            ctx.write_event_to_stream(
                StepCompleteEvent(
                    step_name="critique",
                    status="max_attempts_reached",
                    data={
                        "attempt": ev.attempt,
                        "approved": False,
                        "score": score,
                        "feedback": feedback,
                    },
                )
            )

            return StopEvent(
                result={
                    "article": ev.article,
                    "attempts": ev.attempt,
                    "approved": False,
                    "score": score,
                    "final_feedback": feedback,
                }
            )

        # Loop back to rewrite
        self._logger.info("Article REJECTED. Sending for rewrite with feedback.")

        # Emit generic event to stream
        ctx.write_event_to_stream(
            StepCompleteEvent(
                step_name="critique",
                status="rejected",
                data={
                    "attempt": ev.attempt,
                    "approved": False,
                    "score": score,
                    "feedback": feedback,
                    "action": "rewrite_requested",
                },
            )
        )

        # Return typed event for internal workflow routing (loop)
        return CriticFeedbackEvent(
            topic=ev.topic,
            research=ev.research,
            article=ev.article,
            feedback=feedback,
            attempt=ev.attempt,
        )
