# Facade Pattern

The **Facade Pattern** is a structural design pattern that provides a simplified interface to a complex subsystem. It doesn't change the interfaces; it hides complexity behind a single entry point.

## Core Concept

### Analogy
A hotel concierge is a Facade. Instead of you calling the restaurant, taxi company, and theater box office separately, you just ask the concierge: "Plan my evening." They coordinate everything behind the scenes.

### When to Use
Use Facade when you want to:
- Provide a simple interface to a complex subsystem
- Decouple client code from subsystem internals
- Create a single entry point for a multi-step workflow

---

## Learning Example: Media Player

```python
# Complex subsystem classes
class VideoDecoder:
    def decode(self, file): ...

class AudioDecoder:
    def decode(self, file): ...

class SubtitleParser:
    def parse(self, file): ...

class Screen:
    def render(self, frames): ...

class Speakers:
    def play(self, audio): ...

# The Facade - one simple method for clients
class MediaPlayerFacade:
    def __init__(self):
        self.video = VideoDecoder()
        self.audio = AudioDecoder()
        self.subs = SubtitleParser()
        self.screen = Screen()
        self.speakers = Speakers()

    def play(self, movie_file: str):
        """Simple interface hiding all the complexity."""
        video_frames = self.video.decode(movie_file)
        audio_stream = self.audio.decode(movie_file)
        subtitles = self.subs.parse(movie_file)
        
        self.screen.render(video_frames)
        self.speakers.play(audio_stream)
        # ... synchronize subtitles ...

# Client code - simple!
player = MediaPlayerFacade()
player.play("movie.mp4")
```

---

## Agent Space Example: Article Generation Facade

Instead of the API controller knowing about Research, Writer, and Critic agents, we create a Facade.

### The Problem: Complex Controller

```python
# Without Facade - controller knows too much
@router.post("/articles/generate")
async def generate_article(topic: str):
    research = await research_agent.run(f"Research: {topic}")
    draft = await writer_agent.run(f"Write article based on: {research}")
    critique = await critic_agent.run(f"Critique: {draft}")
    final = await writer_agent.run(f"Revise based on feedback: {critique}")
    return {"article": final}
```

### The Solution: Facade

```python
class ArticleGenerationFacade:
    """
    Facade that hides the complexity of multi-agent article generation.
    """
    def __init__(self):
        self._research = ResearchAgent()
        self._writer = WriterAgent()
        self._critic = CriticAgent()

    async def generate(self, topic: str) -> str:
        """Single entry point - hides all the orchestration."""
        # Step 1: Research
        research = await self._research.run(f"Research: {topic}")
        
        # Step 2: Write
        draft = await self._writer.run(f"Write article based on: {research}")
        
        # Step 3: Critique
        critique = await self._critic.run(f"Critique: {draft}")
        
        # Step 4: Revise
        final = await self._writer.run(f"Revise based on feedback: {critique}")
        
        return final

# Controller is now simple
@router.post("/articles/generate")
async def generate_article(topic: str):
    facade = ArticleGenerationFacade()
    article = await facade.generate(topic)
    return {"article": article}
```

### Benefits
1. **Decoupling**: Controller doesn't know about Research, Writer, Critic agents.
2. **Single Change Point**: If you add a fact-checker step, only the Facade changes.
3. **Testability**: Easy to test the Facade in isolation.

---

## Project Reference

The `BaseAgent.run()` method acts as an implicit Facade:

```python
# agent/agents/base.py
async def run(self, user_msg: str, session_id: Optional[str] = None) -> str:
    # Hides complexity of:
    # - Memory retrieval
    # - LlamaIndex FunctionAgent invocation
    # - Response extraction
    memory = self._get_memory(session_id)
    response = await self.agent.run(user_msg=user_msg, memory=memory)
    return str(response)
```

The caller just says `agent.run("Hello")`. They don't need to know about memory management, LlamaIndex internals, or logging.

---

## Adapter vs Facade

| Aspect | Adapter | Facade |
|--------|---------|--------|
| **Purpose** | Make incompatible interfaces compatible | Simplify a complex subsystem |
| **Interfaces** | Converts one interface to another | Doesn't change interfaces, just hides them |
| **Scope** | Usually wraps ONE class | Wraps MANY classes |
| **Direction** | "I have X, I need it to look like Y" | "I have X, Y, Z — give me one simple entry point" |

