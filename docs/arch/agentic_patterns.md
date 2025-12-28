# Agentic Patterns

This document details the core agentic design patterns implemented in this repository. The architecture leverages LlamaIndex's agent abstractions to create intelligent entities ranging from simple tools to complex, orchestrated teams.

## 1. Single Agents (ReAct Pattern)

The most fundamental unit is the **Single Agent**, implemented using the **ReAct (Reasoning + Acting)** pattern.

-   **Abstraction**: `FunctionAgent` (from `llama_index.core.agent.workflow`)
-   **Behavior**:
    1.  Receives a user query.
    2.  "Reasons" about which tool to use (or if it can answer directly).
    3.  "Acts" by calling the tool.
    4.  Observes the tool output.
    5.  Repeats until the query is answered.

### Examples

-   **`MathAgent`**: Equip with simple calculator functions (`add`, `multiply`). It decomposes complex math problems into sequential tool calls.
-   **`ResearchAgent`**: Uses a `web_search` tool (powered by Perplexity) to gather external information.
-   **`MarketAgent`**: Specialized agent for retrieving financial data. Shows how to secure dangerous operations (like `push_index`) behind Human-in-the-Loop (HITL) checks.

## 2. Multi-Agent Teams

Complex problems often require multiple specialists. We implement two primary coordination patterns:

### A. Handoff Pattern (`MarketResearchTeam`)

In this pattern, agents are peers. An agent can "hand off" control to another agent if it determines the task is better suited for a colleague.

-   **Mechanism**: The `FunctionAgent` is initialized with a `can_handoff_to` list.
-   **Flow**:
    1.  `ResearchAgent` starts with the query.
    2.  If the user asks for "market index updates", the `ResearchAgent` (via LLM reasoning) decides to hand off to `MarketAgent`.
    3.  `MarketAgent` takes over, performs the action, and can hand back or finish.
-   **Pros**: Flexible, natural conversation flow.
-   **Cons**: Can get stuck in loops if not carefully prompted; harder to debug.

### B. Orchestrator Pattern (`ResearchMathOrchestratorTeam`)

In this pattern, a central "Manager" agent directs subordinate agents. The subordinates are often treated as **tools** by the manager.

-   **Mechanism**: Sub-agents are wrapped using `agent.as_tool()`. The manager sees them as functions it can call (`call_research_agent(query="...")`).
-   **Flow**:
    1.  User talks to the `Manager`.
    2.  Manager breaks down the plan.
    3.  Manager calls `call_math_agent` with a sub-task.
    4.  Manager receives the result and aggregates the final answer.
-   **Pros**: Deterministic control, clear hierarchy, easy to enforce standard operating procedures.
-   **Cons**: The manager can become a bottleneck; added latency due to an extra layer of LLM calls.

## 3. Event-Driven Flows

For processes that require strict step-by-step execution, complex branching, or robust state management, we use **LlamaIndex Workflows**.

-   **Abstraction**: `Workflow` class with methods decorated by `@step`.
-   **Concept**: Steps emit **Events**. Other steps listen for specific events. This creates a state machine.

### Example: `StoryCriticFlow`

This flow implements a **Feedback Loop** pattern:

1.  **`research` step**: Gathers data. Emits `ResearchCompleteEvent`.
2.  **`write` step**: Drafts an article. Emits `ArticleWrittenEvent`.
3.  **`critique` step**: Evaluates the article.
    -   **Branch A (Approved)**: Emits `StopEvent` (Flow finishes).
    -   **Branch B (Rejected)**: Emits `CriticFeedbackEvent`.
4.  **`rewrite` step**: Listens for `CriticFeedbackEvent`, rewrites the article, and loops back to `critique`.

This pattern guarantees quality by enforcing a review cycle (up to a configured max attempts).

## 4. Human-in-the-Loop (HITL)

Agents shouldn't always run autonomously, especially for sensitive actions. We implement HITL using the **Interrupt/Resume** pattern.

-   **Trigger**: An agent or workflow step raises an `InputRequiredEvent`.
-   **State Serialization**: The backend serializes the current execution state (including stack, memory, and variables) and returns a "Pending" status to the UI.
-   **User Action**: The UI displays a form. The user provides input.
-   **Resume**: The backend deserializes the state, injects the user's input via `HumanResponseEvent`, and execution continues exactly where it left off.

## 5. Tool Use & Function Calling

Agents interact with the world via Tools.

-   **Definition**: Python functions with type hints and docstrings.
-   **Mechanism**: LlamaIndex converts these into the LLM provider's specific schema (e.g., OpenAI Function Calling API).
-   **Security**: Tools run in the backend environment. Critical tools (like database writes) should be protected by HITL checks or strict validation logic.

