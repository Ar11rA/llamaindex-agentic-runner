# Decorator Pattern

The **Decorator Pattern** is a structural design pattern that allows you to dynamically add behavior to an individual object, either statically or dynamically, without affecting the behavior of other objects from the same class.

It involves a set of decorator classes that are used to wrap concrete components. The decorator implements the same interface as the component it wraps and delegates the main work to the component, while adding its own behavior before or after the delegation.

## Concept: Wrappers (Matryoshka Dolls)

Think of it like nested dolls:
1.  **Inner Doll (Component)**: The real Agent doing the work.
2.  **Outer Doll (Decorator)**: A wrapper that looks like an Agent but adds functionality (e.g., timing, retries) around the inner doll.

## Learning Example: Enhancing Agents

*Note: This pattern is a proposed enhancement for the agent system to add cross-cutting concerns like caching and permissions without modifying core agent logic.*

### Structure

1.  **Component Interface (`AgentProtocol`)**: The interface both the Agent and Decorator implement.
2.  **Concrete Component (`ResearchAgent`)**: The actual object.
3.  **Base Decorator (`AgentDecorator`)**: Maintains a reference to a Component and forwards requests to it.
4.  **Concrete Decorators**: Adds specific behavior.

### Implementation Example

```python
from typing import Protocol

# 1. The Interface (Existing Protocol)
class AgentProtocol(Protocol):
    async def run(self, user_msg: str, session_id: str | None = None) -> str: ...
    # ... other methods

# 2. The Decorator Base Class
class AgentDecorator(AgentProtocol):
    _wrapped_agent: AgentProtocol

    def __init__(self, agent: AgentProtocol):
        self._wrapped_agent = agent

    # Forward identity properties
    @property
    def NAME(self) -> str:
        return self._wrapped_agent.NAME

    # Delegate execution
    async def run(self, user_msg: str, session_id: str | None = None) -> str:
        return await self._wrapped_agent.run(user_msg, session_id)

# 3. Concrete Decorator: Caching
class CachingDecorator(AgentDecorator):
    def __init__(self, agent, cache_client):
        super().__init__(agent)
        self.cache = cache_client

    async def run(self, user_msg: str, session_id: str | None = None) -> str:
        # 1. Check Cache
        cache_key = f"{self.NAME}:{user_msg}"
        cached = await self.cache.get(cache_key)
        if cached:
            return cached

        # 2. Delegate to Real Agent (if not cached)
        result = await super().run(user_msg, session_id)
        
        # 3. Save to Cache
        await self.cache.set(cache_key, result)
        return result

# 4. Concrete Decorator: RBAC (Permissions)
class PermissionDecorator(AgentDecorator):
    def __init__(self, agent, user_role: str):
        super().__init__(agent)
        self.user_role = user_role

    async def run(self, user_msg: str, session_id: str | None = None) -> str:
        # 1. Check Permissions
        if "execute trade" in user_msg and self.user_role != "premium":
            return "⛔ Access Denied"
        
        # 2. Delegate
        return await super().run(user_msg, session_id)
```

### Usage (Runtime Composition)

You can stack decorators dynamically at runtime:

```python
# Create the base agent
agent = MarketAgent()

# Wrap 1: Add Permissions
safe_agent = PermissionDecorator(agent, user_role="guest")

# Wrap 2: Add Caching to the safe agent
cached_safe_agent = CachingDecorator(safe_agent, cache_client)

# Run it
# This will check Cache -> Check Permissions -> Run MarketAgent
await cached_safe_agent.run("execute trade AAPL")
```

### Real-World Use Cases

1.  **Caching**: Save API costs by caching common queries for `ResearchAgent` or `WriterAgent`.
2.  **Permissions (RBAC)**: Restrict sensitive actions (trading, database writes) in `MarketAgent` based on user roles without polluting business logic.
3.  **Circuit Breaker**: Detect failures in downstream APIs (e.g., Anthropic is down) and fail fast to prevent system hangs.
4.  **Rate Limiting**: Limit how many requests a specific user/session can make to an expensive agent per minute.

### Distinction: Python Decorators vs. Design Pattern

*   **Python Decorators (`@decorator`)**: Compile-time function wrapping (Meta-programming). Used for static, permanent behavior changes (e.g., `@step` in flows).
*   **Decorator Pattern**: Runtime object composition. Used for flexible, stackable behavior that can be toggled per-instance.

