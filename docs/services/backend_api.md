# Backend API Service

The Backend service is the core of the LlamaIndex Agents application. It provides the intelligence layer, hosting various agents, teams, and workflows, and exposing them via a RESTful API.

## Technology Stack

-   **Framework**: FastAPI (Python)
-   **AI/LLM Framework**: LlamaIndex
-   **Database ORM**: SQLAlchemy with `asyncpg` for asynchronous PostgreSQL access
-   **Server**: Uvicorn

## Directory Structure (`agent/`)

-   `api/`: API route definitions and controllers.
    -   `v1/`: Version 1 of the API endpoints.
    -   `dto/`: Data Transfer Objects (Pydantic models) for request/response validation.
-   `agents/`: Definitions of individual LlamaIndex agents (e.g., `research_agent.py`, `market_agent.py`).
-   `teams/`: Definitions of agent teams/orchestrators.
-   `flows/`: LlamaIndex Workflows for complex logic (e.g., Story Critic flow).
-   `tools/`: Custom tools used by agents (e.g., market research tools, math tools).
-   `config/`: Configuration for database, observability, and LLMs.
-   `main.py`: Application entry point and lifecycle management.

## Key Concepts

### Agents
Standalone intelligent entities capable of performing specific tasks. They utilize tools to interact with external data or perform calculations.
-   **Endpoint**: `/api/v1/agents`
-   **Implementation**: Subclasses of `BaseAgent` or configured `FunctionCallingAgent` instances.

### Teams
Groups of agents orchestrated to solve complex problems. A "manager" or "orchestrator" agent typically delegates tasks to sub-agents.
-   **Endpoint**: `/api/v1/teams`
-   **Implementation**: Hierarchical agent structures.

### Flows
Directed workflows that define a strict or state-machine-based execution path. Flows are ideal for processes requiring:
-   Step-by-step execution.
-   Human-in-the-Loop (HITL) interactions.
-   Complex branching logic.
-   **Endpoint**: `/api/v1/flows`

## API Endpoints

### General
-   `GET /health`: Health check endpoint.

### Agents API (`/api/v1/agents`)
-   `GET /`: List all available agents.
-   `POST /{agent_id}/chat/stream`: Stream a chat conversation with a specific agent.
-   `POST /{agent_id}/chat/stream/respond`: Provide human input to a paused agent execution (if applicable).
-   `DELETE /{agent_id}/session/{session_id}`: Clear chat memory for a session.

### Teams API (`/api/v1/teams`)
-   `GET /`: List all available teams.
-   `POST /{team_id}/chat/stream`: Stream a chat with a team.
-   `DELETE /{team_id}/session/{session_id}`: Clear team session memory.

### Flows API (`/api/v1/flows`)
-   `GET /`: List all available flows.
-   `POST /{flow_id}/stream`: Run a flow and stream events/results.
-   `POST /{flow_id}/run/async`: Start a flow run asynchronously (returns a run ID).
-   `GET /{flow_id}/run/{run_id}`: Poll the status of an async run.
-   `POST /{flow_id}/run/respond`: Provide input for a HITL flow.

## Streaming & SSE

The backend uses Server-Sent Events (SSE) to stream responses. This allows for real-time updates as the agent "thinks" or as steps in a flow complete.

**Event Types:**
-   `token`: A partial text token (for streaming LLM responses).
-   `agent`: Event indicating which agent is currently active.
-   `flow_event`: Progress update from a workflow step.
-   `hitl`: Request for human intervention (Human-in-the-Loop).
-   `done`: Stream completion.

## Configuration

Configuration is managed via environment variables and the `config/` module.

-   **Database**: Configured in `config/database.py`. Uses `MEMORY_DATABASE_URI`.
-   **LLMs**: Configured in `config/llm_factory.py`. Supports OpenAI and custom models.
-   **Observability**: Configured in `config/observability.py`. Integrates with Arize Phoenix.

## Development

To run the backend locally:

```bash
cd agent
# Install dependencies
pip install -e .
# Run server
python main.py
```

