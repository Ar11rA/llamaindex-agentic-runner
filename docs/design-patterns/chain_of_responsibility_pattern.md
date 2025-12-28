# Chain of Responsibility Pattern

The **Chain of Responsibility Pattern** is a behavioral design pattern that lets you pass requests along a chain of handlers. Upon receiving a request, each handler decides either to process the request or to pass it to the next handler in the chain.

## Core Concept

### Analogy: Tech Support Tiers
1.  **Tier 1 (Chatbot)**: Can handle "Reset Password". If not, pass to Tier 2.
2.  **Tier 2 (Human Support)**: Can handle "Billing Issue". If not, pass to Tier 3.
3.  **Tier 3 (Engineer)**: Can handle "Bug Report".

The customer sends the request to the system, not a specific person. The system routes it until someone solves it.

### Structure
1.  **Handler Interface**: Declares a method for building the chain and executing a request.
2.  **Base Handler**: Optional class implementing the boilerplate (storing `next_handler`).
3.  **Concrete Handlers**: Contain the actual processing logic.

---

## Learning Example: Middleware Pipeline

```python
from abc import ABC, abstractmethod
from typing import Optional

# 1. Handler Interface
class Handler(ABC):
    @abstractmethod
    def set_next(self, handler: "Handler") -> "Handler": ...
    
    @abstractmethod
    def handle(self, request: str) -> Optional[str]: ...

# 2. Base Handler
class AbstractHandler(Handler):
    _next_handler: Optional[Handler] = None

    def set_next(self, handler: Handler) -> Handler:
        self._next_handler = handler
        return handler

    def handle(self, request: str) -> Optional[str]:
        if self._next_handler:
            return self._next_handler.handle(request)
        return None

# 3. Concrete Handlers
class AuthHandler(AbstractHandler):
    def handle(self, request: str) -> Optional[str]:
        if "token=123" not in request:
            return "403 Forbidden"
        print("Auth Passed")
        return super().handle(request)

class CacheHandler(AbstractHandler):
    def handle(self, request: str) -> Optional[str]:
        if "cached_query" in request:
            return "Returning Cached Result"
        print("Cache Miss")
        return super().handle(request)

class AgentHandler(AbstractHandler):
    def handle(self, request: str) -> Optional[str]:
        return f"Agent Response to: {request}"

# Usage
# Build the chain: Auth -> Cache -> Agent
auth = AuthHandler()
cache = CacheHandler()
agent = AgentHandler()

auth.set_next(cache).set_next(agent)

# Test 1: Blocked
print(auth.handle("query=hello")) 
# Output: "403 Forbidden"

# Test 2: Success
print(auth.handle("query=hello token=123"))
# Output: Auth Passed -> Cache Miss -> "Agent Response..."
```

---

## Agent Space Example: Request Processing Pipeline

Ideal for implementing robust agent systems with **Guardrails**.

1.  **SafetyFilter**: Checks for PII or toxicity.
2.  **TopicFilter**: Ensures the query is relevant (e.g., "Only finance questions").
3.  **LanguageFilter**: Detects language and translates if needed.
4.  **Agent**: Finally generates the answer.

### Benefits
*   **Decoupling**: The Agent doesn't need to know about Auth or Safety logic.
*   **Flexibility**: You can reorder the chain (e.g., put Cache before Auth for public data) at runtime.
*   **Single Responsibility**: Each class does one thing (Auth, Cache, or Safety).


