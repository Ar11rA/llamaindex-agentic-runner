# Observer Pattern

The **Observer Pattern** is a behavioral design pattern that lets you define a subscription mechanism to notify multiple objects about any events that happen to the object they're observing.

## Learning Example: Async Auditing & Monitoring

*Note: This pattern is not currently implemented in the core codebase but is a recommended addition for handling cross-cutting concerns like auditing, logging, and UI updates.*

### Structure

1.  **Subject (`ObservableAgent`)**: The component doing the work (the Agent).
2.  **Observer (`AgentObserver`)**: The interface for components that want to listen.
3.  **Concrete Observers**: Specific implementations (Logger, DatabaseAudit, WebSocketNotifier).

### Implementation Example

```python
import asyncio
from abc import ABC, abstractmethod
from typing import List

# 1. The Observer Interface
class AgentObserver(ABC):
    """
    Observer interface for receiving updates from an Agent.
    """
    @abstractmethod
    def on_agent_run_start(self, agent_name: str, input_query: str) -> None:
        pass

    @abstractmethod
    def on_agent_run_complete(self, agent_name: str, response: str) -> None:
        pass

    @abstractmethod
    def on_agent_error(self, agent_name: str, error: Exception) -> None:
        pass

# 2. Concrete Observer: Async Auditing
class AsyncAuditObserver(AgentObserver):
    """
    An observer that performs auditing asynchronously 
    so it doesn't block the main agent execution.
    """
    
    def on_agent_run_complete(self, agent_name: str, response: str) -> None:
        # Instead of writing to DB directly, we schedule a task
        print(f"[{agent_name}] Execution finished. Scheduling audit...")
        asyncio.create_task(self._write_audit_log(agent_name, response))

    async def _write_audit_log(self, agent_name: str, data: str):
        """Simulate a slow network/DB call"""
        await asyncio.sleep(2)  # Simulate network latency
        # logic to write to audit_table in DB
        print(f"✅ [AUDIT] Successfully archived run for {agent_name}")

    def on_agent_run_start(self, agent_name: str, input_query: str) -> None:
        pass
        
    def on_agent_error(self, agent_name: str, error: Exception) -> None:
        pass

# 3. The Subject (Mixin)
class ObservableAgent:
    """
    A mixin that implements the Subject part of Observer pattern.
    """
    def __init__(self):
        self._observers: List[AgentObserver] = []

    def attach(self, observer: AgentObserver) -> None:
        if observer not in self._observers:
            self._observers.append(observer)

    def notify_complete(self, agent_name: str, response: str) -> None:
        for observer in self._observers:
            observer.on_agent_run_complete(agent_name, response)

# 4. Usage in Agent
class ResearchAgentWithObservers(ObservableAgent):
    NAME = "research"
    
    def __init__(self):
        super().__init__()
        # ... init logic ...

    async def run(self, user_msg: str) -> str:
        # ... logic ...
        result = "Search results..."
        
        # Notify observers (Auditor, Logger, UI)
        self.notify_complete(self.NAME, result)
        return result
```

### Benefits
1.  **Decoupling**: The Agent logic doesn't need to know about Auditing, WebSocket updates, or Billing. It just notifies "I'm done".
2.  **Performance**: Heavy tasks (like DB writes) can be offloaded to async observers without blocking the user response.
3.  **Extensibility**: You can add new behaviors (e.g., "Send Slack Notification on Error") without modifying the Agent's core code.

