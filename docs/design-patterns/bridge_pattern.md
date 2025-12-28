# Bridge Pattern

The **Bridge Pattern** is a structural design pattern that decouples an **abstraction** from its **implementation** so that the two can vary independently.

## Core Concept

### Analogy: Universal Remote
- **Abstraction**: The Remote Control (Has buttons: On, Off, Vol+, Vol-).
- **Implementation**: The Device (TV, Radio, Projector).
- **Bridge**: The protocol (IR signal) connecting them.

You can create new types of Remotes (TouchScreenRemote, VoiceRemote) without changing the Devices.
You can create new types of Devices (SmartTV, Hologram) without changing the Remotes.

### When to Use
- You want to avoid a Cartesian product of classes (e.g., `WindowsWindow`, `LinuxWindow`, `MacWindow`, `WindowsDialog`, `LinuxDialog`...).
- You have two independent dimensions of variation (e.g., Platform vs. UI Component).

---

## Learning Example: Shapes and Colors

Without Bridge, you'd need `RedCircle`, `BlueCircle`, `RedSquare`, `BlueSquare` (4 classes).
With Bridge, you have `Shape` (2 classes) + `Color` (2 classes) = 4 classes, but it scales linearly (N+M) instead of exponentially (N*M).

```python
from abc import ABC, abstractmethod

# 1. Implementation Interface (The "Color")
class Color(ABC):
    @abstractmethod
    def fill(self): ...

class Red(Color):
    def fill(self): return "Red"

class Blue(Color):
    def fill(self): return "Blue"

# 2. Abstraction (The "Shape")
class Shape(ABC):
    def __init__(self, color: Color):
        self.color = color  # The Bridge

    @abstractmethod
    def draw(self): ...

# 3. Refined Abstractions
class Circle(Shape):
    def draw(self):
        print(f"Drawing Circle in {self.color.fill()}")

class Square(Shape):
    def draw(self):
        print(f"Drawing Square in {self.color.fill()}")

# Usage - Mix and Match
red_circle = Circle(Red())
blue_square = Square(Blue())

red_circle.draw()
blue_square.draw()
```

---

## Agent Space Example: Agents & Memory Backends

Imagine you have different types of Agents (Research, Chat) and different Memory backends (Redis, Postgres).

### The Problem (Without Bridge)
You'd need `RedisResearchAgent`, `PostgresResearchAgent`, `RedisChatAgent`, etc.

### The Solution (With Bridge)

```python
# 1. Implementation: Storage Backend
class MemoryBackend(ABC):
    @abstractmethod
    def save(self, key, value): ...

class RedisBackend(MemoryBackend):
    def save(self, key, value): print(f"Redis SET {key}={value}")

class PostgresBackend(MemoryBackend):
    def save(self, key, value): print(f"INSERT INTO {key} VALUES {value}")

# 2. Abstraction: Agent
class Agent(ABC):
    def __init__(self, memory: MemoryBackend):
        self.memory = memory  # Bridge

    def remember(self, fact):
        self.memory.save("fact", fact)

# 3. Refined Abstraction
class ResearchAgent(Agent):
    def remember(self, fact):
        print("ResearchAgent storing data...")
        super().remember(fact)

# Usage
agent = ResearchAgent(RedisBackend())
agent.remember("Python is cool")
```

---

## Bridge vs Strategy vs Adapter

| Pattern | Type | Intent |
|---------|------|--------|
| **Bridge** | Structural | **Avoid class explosion** (N*M). Decouple abstraction from implementation so both can grow independently. |
| **Strategy** | Behavioral | **Swap algorithms** at runtime. The context stays the same, only the logic inside changes. |
| **Adapter** | Structural | **Make incompatible interfaces work**. Fixes a "square peg in round hole" problem *after* code exists. |

**Confusion Check:**
Bridge and Strategy look identical in code (`class A has a B`). The difference is **Intent**:
- **Strategy**: "I want to plug in a different sorting algorithm."
- **Bridge**: "I want `Window` types and `OS` types to evolve separately."


