# Composite Pattern

The **Composite Pattern** is a structural design pattern that lets you compose objects into tree structures and then work with these structures as if they were individual objects.

## Core Concept: "Treat the Whole like the Part"

### Analogy
Think of a file system.
- **File (Leaf)**: A single unit.
- **Folder (Composite)**: Can contain files *and* other folders.
- **Uniformity**: You can "delete" a file OR a folder (which recursively deletes everything inside). The client treats both uniformly.

### Structure
1.  **Component**: Common interface for both Leaf and Composite.
2.  **Leaf**: Simple object that does the work.
3.  **Composite**: Container that delegates work to its children.

## Learning Example: Hierarchical Teams

```python
from typing import Protocol

# 1. Component (Interface)
class AgentComponent(Protocol):
    async def run(self, task: str) -> str: ...

# 2. Leaf (Single Agent)
class SingleAgent(AgentComponent):
    def __init__(self, name):
        self.name = name

    async def run(self, task: str) -> str:
        return f"[{self.name}] Completed: {task}"

# 3. Composite (Team of Agents)
class AgentTeam(AgentComponent):
    def __init__(self, name):
        self.name = name
        self.members: list[AgentComponent] = []

    def add(self, member: AgentComponent):
        self.members.append(member)

    async def run(self, task: str) -> str:
        results = []
        results.append(f"Team {self.name} starting...")
        # Delegate to children (can be single agents OR other teams!)
        for member in self.members:
            results.append(await member.run(task))
        return "\n".join(results)

# 4. Usage (Client treats Team and Agent the same)
researcher = SingleAgent("Researcher")
writer = SingleAgent("Writer")

# Create a sub-team
content_team = AgentTeam("Content Squad")
content_team.add(researcher)
content_team.add(writer)

# Create a top-level team that contains the sub-team
company = AgentTeam("The Company")
company.add(content_team)      # Add Composite
company.add(SingleAgent("CEO")) # Add Leaf

# Run the whole structure with one call
await company.run("Make a report")
```

### Benefits
1.  **Simplifies Client Code**: The client doesn't need to know if it calls a single agent or a complex hierarchy.
2.  **Scalability**: Easy to add new types of components (e.g., a "ParallelTeam" composite) without breaking existing code.


