# Testing Guide

This guide covers the testing strategy for the LlamaIndex Agents application, including how to run unit tests and how to perform manual testing of the system.

## 1. Unit Testing

The backend uses `pytest` for unit testing. The tests are located in `agent/tests/`.

### Test Structure

-   **`tests/unit/`**: Isolated unit tests for individual components.
    -   `test_agents.py`: Verifies agent initialization, configuration, and tool registration.
    -   `test_llm_factory.py`: Tests the LLM provider factory logic.
    -   `test_tools.py`: Tests the logic of individual tools (Math, Research, etc.).
-   **`tests/api/`**: Tests for FastAPI endpoints (using `TestClient`).
-   **`tests/conftest.py`**: Shared fixtures (mocks for Database, LLM, Settings).

### Mocks & Fixtures

We use extensive mocking to avoid making real API calls during tests.
-   **`mock_llm`**: Simulates LlamaIndex LLM responses.
-   **`mock_db_manager`**: Mocks the PostgreSQL database connection and queries.
-   **`mock_settings`**: Overrides environment variables (disables observability, uses fake API keys).

### Running Tests

1.  Navigate to the backend directory:
    ```bash
    cd agent
    ```

2.  Run all tests using `uv`:
    ```bash
    uv run pytest
    ```

3.  Run specific tests:
    ```bash
    # Run only agent tests
    uv run pytest tests/unit/test_agents.py

    # Run tests with verbose output
    uv run pytest -v
    ```

## 2. Manual Testing

Since this is an agentic application, manual testing is crucial to verify the "reasoning" capabilities and end-to-end flows.

### Prerequisites
-   Ensure the full stack is running (`docker-compose up`).
-   Frontend: `http://localhost:3000`
-   Phoenix: `http://localhost:6006`

### Test Cases

#### A. Single Agent Chat (MathAgent)
1.  **Select Agent**: Go to "Agents" -> "Math Agent".
2.  **Input**: "What is 153 plus 482?"
3.  **Expected Behavior**:
    -   Agent should respond with "635".
    -   In Phoenix Traces, you should see a `tool_call` to `add(a=153, b=482)`.

#### B. Tool-Using Agent (ResearchAgent)
1.  **Select Agent**: "Agents" -> "Research Agent".
2.  **Input**: "What are the latest updates on LlamaIndex?"
3.  **Expected Behavior**:
    -   Agent should stream a response citing recent information.
    -   In Phoenix Traces, you should see a `tool_call` to `web_search`.

#### C. Handoff Team (MarketResearchTeam)
1.  **Select Team**: "Teams" -> "Market Research Team".
2.  **Input**: "Research the current price of AAPL and then update the market index."
3.  **Expected Behavior**:
    -   **Step 1**: Research agent searches for AAPL price.
    -   **Step 2**: Research agent hands off to Market agent.
    -   **Step 3 (HITL)**: Market agent attempts `push_index`. **System should PAUSE**.
    -   **UI**: A "Human Input Required" form should appear asking for confirmation (yes/no).
    -   **Step 4**: Type "yes".
    -   **Final**: Market agent confirms the update.

#### D. Orchestrator Team (ResearchMathOrchestratorTeam)
1.  **Select Team**: "Teams" -> "Research & Math Orchestrator".
2.  **Input**: "Find the population of France and multiply it by 2."
3.  **Expected Behavior**:
    -   Manager agent plans the task.
    -   Calls `ResearchAgent` (as tool) to get population.
    -   Calls `MathAgent` (as tool) to multiply the result.
    -   Returns the final number.

#### E. Workflow Loop (StoryCriticFlow)
1.  **Select Flow**: "Flows" -> "Story Critic Flow".
2.  **Input**: "Write a short story about a space cat."
3.  **Expected Behavior**:
    -   **Research Step**: Simulates research.
    -   **Write Step**: Generates draft.
    -   **Critique Step**: Reviewer evaluates draft.
        -   *Likely*: Reviewer rejects draft (simulated or real LLM critique).
    -   **Rewrite Step**: Writer improves draft.
    -   **Loop**: Continues until approved or max attempts reached.
    -   **Final Output**: Displays the final story.

### Troubleshooting Manual Tests
-   **No Response?**: Check Backend logs (`docker-compose logs -f backend`). Look for exceptions.
-   **Stuck on Streaming?**: Check network tab in browser. Ensure SSE connection is open.
-   **HITL Not Appearing?**: Verify the agent actually triggered the tool that requires permission.


