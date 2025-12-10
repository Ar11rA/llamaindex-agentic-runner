# Template Method Pattern

The **Template Method Pattern** is a behavioral design pattern that defines the skeleton of an algorithm in the superclass but lets subclasses override specific steps of the algorithm without changing its structure.

This is the core architectural pattern used for Agents and Teams in this project.

## Project Example: `BaseAgent`

The `BaseAgent` class defines the common initialization and execution flow for all agents, but defers the specific tool definition to subclasses via the abstract `get_tools()` method.

```python:agent/agents/base.py
class BaseAgent(ABC):
    """
    Abstract base class for all agents.
    """
    
    # Template steps that must be defined by subclasses
    NAME: str
    DESCRIPTION: str
    DEFAULT_SYSTEM_PROMPT: str

    def __init__(self, ...):
        # Common initialization logic (The "Template")
        self.system_prompt = system_prompt or self.DEFAULT_SYSTEM_PROMPT
        
        # Hook for subclasses to provide specific behavior
        self.tools = self.get_tools()
        
        self.agent = FunctionAgent(
            name=self.NAME,
            tools=self.tools,
            # ...
        )

    @abstractmethod
    def get_tools(self) -> List[Callable[..., Any]]:
        """Return the list of tools for this agent. Must be implemented by subclasses."""
        ...
```

**Subclass Implementation (`ResearchAgent`):**

```python:agent/agents/research_agent.py
class ResearchAgent(BaseAgent):
    NAME = "research"
    # ...
    
    def get_tools(self) -> List[Callable[..., Any]]:
        # Specific implementation for Research Agent
        return [web_search]
```

## Project Example: `BaseTeam`

Similarly, `BaseTeam` defines how a team operates but delegates the agent composition to subclasses.

```python:agent/teams/base.py
class BaseTeam(ABC):
    def __init__(self, timeout: float = 600.0):
        # Template: Initialize team structure
        
        # Step: Get agents (implemented by subclass)
        agents = self.get_agents()
        
        # Step: Get root agent (implemented by subclass)
        root = self.get_root_agent()
        
        # Common logic: Build the workflow
        self.workflow = AgentWorkflow(agents=agents, root_agent=root, ...)

    @abstractmethod
    def get_agents(self) -> List[FunctionAgent]:
        ...

    @abstractmethod
    def get_root_agent(self) -> str:
        ...
```

### Benefits in this Project
1.  **Code Reuse**: Common logic (initialization, logging, HITL handling, memory management) is written once in the base class.
2.  **Enforced Structure**: Subclasses *must* implement the abstract methods, ensuring all agents/teams adhere to the correct contract.
3.  **Flexibility**: New agents can be added easily by just defining their tools and name, without worrying about the underlying execution engine.

