# Memento Pattern

The **Memento Pattern** is a behavioral design pattern that lets you save and restore the previous state of an object without revealing the details of its implementation.

In this project, we use the Memento pattern to handle **Human-in-the-Loop (HITL)** workflows. When an agent needs human input, we snapshot its entire execution state (the memento), save it to the database, and later restore it to resume execution.

## Project Example: HITL State Management

In `BaseAgent`, we capture the workflow state when an `InputRequiredEvent` occurs.

### 1. Creating the Memento (Snapshot)

```python:agent/agents/base.py
    async def run_with_hitl(self, ...):
        # ... execution ...
        async for event in handler.stream_events():
            if isinstance(event, InputRequiredEvent):
                
                # [MEMENTO CREATION]
                # Serialize the entire context (execution stack, variables, history)
                ctx_dict = handler.ctx.to_dict()
                
                # Return the memento to be saved (e.g., in DB)
                return HITLPendingResult(
                    workflow_id=workflow_id,
                    prompt=event.prefix,
                    context_dict=ctx_dict,  # <-- The Memento
                    user_name=getattr(event, "user_name", "operator"),
                )
```

### 2. Restoring from Memento

When the user responds, we re-create the context from the saved dictionary.

```python:agent/agents/base.py
    async def resume_with_input(
        self,
        context_dict: dict,  # <-- The Memento
        human_response: str,
        # ...
    ) -> RunResult:
        
        # [MEMENTO RESTORATION]
        # Rehydrate the context object from the dictionary
        ctx = Context.from_dict(self.agent, context_dict)

        # Restore memory (if separate)
        memory = self._get_memory(session_id)
        if memory:
            await ctx.store.set("memory", memory)

        # Resume the workflow using the restored context
        handler = self.agent.run(ctx=ctx)
        
        # ... continue execution ...
```

### Benefits in this Project
1.  **Statelessness**: The API server can remain stateless. The complex state of a running agent workflow is offloaded to the database and restored only when needed.
2.  **Long-running Processes**: A workflow can pause for days waiting for user input without consuming server memory.
3.  **Resilience**: If the server restarts, the state is preserved in the memento (persisted in DB), allowing the workflow to resume seamlessly.

