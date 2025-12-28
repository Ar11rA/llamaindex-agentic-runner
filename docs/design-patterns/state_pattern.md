# State Pattern

The **State Pattern** allows an object to alter its behavior when its internal state changes. The object will appear to change its class.

It is about replacing **massive if/else blocks** (based on status flags) with **polymorphic classes**.

## Core Concept

### Analogy
A Document Workflow (`Draft` → `Review` → `Published`).
- In `Draft`, `publish()` moves it to `Review`.
- In `Review`, `publish()` moves it to `Published`.
- In `Published`, `publish()` does nothing.

Instead of one big `if state == 'Draft'` block, each state is a separate class with its own implementation of `publish()`.

## Learning Example: Agent Moods

Imagine an agent that behaves differently based on its "Mood".

```python
from abc import ABC, abstractmethod

# 1. State Interface
class AgentState(ABC):
    @abstractmethod
    def handle_request(self, agent, query: str) -> str: ...

# 2. Concrete States
class HappyState(AgentState):
    def handle_request(self, agent, query: str) -> str:
        if "bad news" in query:
            agent.change_state(SadState())  # Transition
            return "Oh no! 😢"
        return f"Sure! I'd love to help with: {query} 😊"

class SadState(AgentState):
    def handle_request(self, agent, query: str) -> str:
        if "cheer up" in query:
            agent.change_state(HappyState()) # Transition
            return "Thanks, I feel better! 😄"
        return f"Sigh... okay, I'll do: {query} 😞"

# 3. Context (The Agent)
class MoodAgent:
    def __init__(self):
        self.state: AgentState = HappyState()  # Initial state

    def change_state(self, new_state: AgentState):
        self.state = new_state

    def run(self, query: str) -> str:
        # DELEGATION: Ask the state to handle it
        return self.state.handle_request(self, query)

# Usage
agent = MoodAgent()
print(agent.run("Hello"))        # "Sure! ... 😊" (Happy)
print(agent.run("bad news"))     # "Oh no! 😢" (Switches to Sad)
print(agent.run("Do work"))      # "Sigh... okay ... 😞" (Sad behavior)
```

## The Role of Delegation

The State Pattern relies on **Delegation**.
- The Context (`MoodAgent`) **delegates** the work to the current State object.
- `self.state.handle_request(...)`

### When to Use
- You have an object with **3+ states** and complex transitions.
- You have massive `if/elif/else` blocks checking `self.state`.

### When NOT to Use
- Simple boolean flags (`is_active`).
- If the behavior doesn't change drastically between states (just simple data changes).


