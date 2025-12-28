# Mediator Pattern

The **Mediator Pattern** is a behavioral design pattern that restricts direct communications between objects and forces them to collaborate only via a mediator object. This reduces chaotic dependencies between interacting objects.

## Core Concept

### Analogy: Air Traffic Control (ATC)
*   **Without Mediator**: Every pilot talks to every other pilot ("Flight 747, I'm landing, you move!"). Chaos.
*   **With Mediator**: Pilots only talk to ATC ("Requesting landing"). ATC tells other planes to hold. Pilots don't need to know about each other.

### When to Use
*   You have a set of objects that communicate in complex, coupled ways (spaghetti code).
*   You want to reuse an object, but it's hard because it refers to many other objects.

---

## Learning Example: Chat Room

```python
from abc import ABC, abstractmethod

# 1. Mediator Interface
class ChatMediator(ABC):
    @abstractmethod
    def send_message(self, msg: str, user: "User"): ...

# 2. Concrete Mediator
class ChatRoom(ChatMediator):
    def __init__(self):
        self.users = []

    def add_user(self, user):
        self.users.append(user)

    def send_message(self, msg: str, sender: "User"):
        for user in self.users:
            # Don't send to self
            if user != sender:
                user.receive(msg)

# 3. Colleague (The Users)
class User(ABC):
    def __init__(self, mediator: ChatMediator, name: str):
        self.mediator = mediator
        self.name = name

    def send(self, msg: str):
        print(f"{self.name} sends: {msg}")
        self.mediator.send_message(msg, self)

    def receive(self, msg: str):
        print(f"{self.name} received: {msg}")

# Usage
mediator = ChatRoom()
alice = User(mediator, "Alice")
bob = User(mediator, "Bob")
charlie = User(mediator, "Charlie")

mediator.add_user(alice)
mediator.add_user(bob)
mediator.add_user(charlie)

alice.send("Hello everyone!")
# Bob received: Hello everyone!
# Charlie received: Hello everyone!
```

---

## Agent Space Example: Orchestrator Team

In your project, the `ResearchMathOrchestratorTeam` is a Mediator.

### The Problem (Without Mediator)
*   `ResearchAgent` needs to call `MathAgent` to calculate stats.
*   `MathAgent` needs to call `WriterAgent` to format results.
*   **Result**: Tight coupling. You can't use `ResearchAgent` alone because it crashes without `MathAgent`.

### The Solution (Mediator)
*   **Orchestrator (Mediator)**: Holds references to all agents.
*   **Agents (Colleagues)**: Just do their job and return results. They don't know who is next.

```python
class Orchestrator(Mediator):
    def __init__(self):
        self.researcher = ResearchAgent()
        self.mathematician = MathAgent()
        self.writer = WriterAgent()

    async def run_workflow(self, topic: str):
        # 1. Mediator calls Researcher
        data = await self.researcher.run(topic)
        
        # 2. Mediator analyzes data, decides to call Math
        if "calculate" in data:
            result = await self.mathematician.run(data)
            data += f"\nStats: {result}"
            
        # 3. Mediator calls Writer
        report = await self.writer.run(data)
        return report
```

### Benefits
*   **Decoupling**: `ResearchAgent` works in isolation. It doesn't depend on `MathAgent`.
*   **Centralized Control**: The workflow logic resides in one place (the Orchestrator), making it easy to change the flow.

---

## Mediator vs Chain of Responsibility vs Observer

| Pattern | Topology | Intent |
|---------|----------|--------|
| **Chain of Responsibility** | Linear (1 -> 2 -> 3) | "Pass it down until someone handles it" |
| **Mediator** | Star (Hub & Spoke) | "I'll coordinate how you all talk to each other" |
| **Observer** | One-to-Many | "I'll let you all know when something happens" |


