# System Architecture

The LlamaIndex Agents application is a modern full-stack application designed to orchestrate and interact with intelligent agents, teams of agents, and workflows. It uses a containerized microservices architecture to ensure scalability, maintainability, and ease of deployment.

## High-Level Overview

The system consists of four main services:

1.  **Frontend (UI)**: A React-based single-page application (SPA) that provides a chat interface for users to interact with agents and workflows.
2.  **Backend (API)**: A Python FastAPI application that hosts the LlamaIndex agents, orchestrates workflows, and manages state.
3.  **Database (PostgreSQL)**: A relational database used for persisting agent state, chat history, and other application data.
4.  **Observability (Arize Phoenix)**: A tracing and observability platform for monitoring LLM applications.

## Service Interaction Diagram

```mermaid
graph TD
    User[User Browser] -->|HTTP/WebSocket| Frontend[Frontend (Nginx/React)]
    Frontend -->|API Requests| Backend[Backend (FastAPI)]
    Backend -->|Read/Write State| Postgres[(PostgreSQL)]
    Backend -->|Trace/Log| Phoenix[Arize Phoenix]
    Backend -->|LLM Calls| OpenAI[OpenAI API]
    Backend -->|Search| Perplexity[Perplexity API]
```

## Detailed Component Breakdown

### 1. Frontend Service (`agent-ui`)
-   **Tech Stack**: React, TypeScript, Vite, Tailwind CSS.
-   **Port**: 3000 (mapped from internal 80).
-   **Role**: Serves the user interface. It handles user input, displays chat messages, and manages real-time updates via Server-Sent Events (SSE).
-   **Deployment**: Built as a static site and served via Nginx in a Docker container. Nginx also acts as a reverse proxy for API calls in production-like setups (though the docker-compose often maps ports directly).

### 2. Backend Service (`agent`)
-   **Tech Stack**: Python 3.11+, FastAPI, LlamaIndex, SQLAlchemy (asyncpg).
-   **Port**: 6001.
-   **Role**: The core intelligence engine.
    -   **Agents**: Individual LlamaIndex agents (e.g., Research, Market Analysis).
    -   **Teams**: Orchestrator agents that manage multiple sub-agents.
    -   **Flows**: LlamaIndex Workflows for complex, multi-step processes with human-in-the-loop capabilities.
-   **API**: Exposes a RESTful API (v1) for listing entities, managing sessions, and streaming chat responses.

### 3. Database Service (`postgres`)
-   **Image**: `postgres:16-alpine`.
-   **Port**: 5432.
-   **Role**: Persistent storage.
-   **Data**: Stores chat history (memory) for agents and potentially application configuration.
-   **Access**: Accessed by the Backend service via the `asyncpg` driver.

### 4. Observability Service (`phoenix`)
-   **Image**: `arizephoenix/phoenix:latest`.
-   **Port**: 6006 (UI).
-   **Role**: Provides visibility into LLM execution.
-   **Features**: Traces LLM calls, visualizes chains/agents, and helps debug latency or quality issues.

## Data Flow

1.  **Chat Interaction**:
    -   User sends a message via the Frontend.
    -   Frontend sends a POST request to the Backend (e.g., `/api/v1/agents/{id}/chat/stream`).
    -   Backend processes the request, invoking the appropriate LlamaIndex agent.
    -   Agent interacts with LLMs (OpenAI) and Tools (Perplexity, etc.).
    -   Intermediate steps and final response are streamed back to the Frontend via SSE.
    -   Chat history is saved to PostgreSQL.
    -   Execution traces are sent to Phoenix.

2.  **Human-in-the-Loop (HITL)**:
    -   Some workflows (Flows) may pause for user input.
    -   The Backend notifies the Frontend of a "pause" event.
    -   Frontend displays an input form.
    -   User provides input, which is sent back to resume the workflow.

## Deployment

The entire stack is defined in `docker-compose.yml` for easy local development and deployment.

-   **Networking**: All services share a default bridge network.
-   **Volumes**: Persistent volumes are used for Postgres data (`postgres_data`) and Phoenix data (`phoenix_data`).
-   **Configuration**: Environment variables (e.g., `OPENAI_API_KEY`) are passed to the Backend service.

## Software Architecture Patterns

The codebase follows several key software design patterns to ensure modularity and extensibility:

| Pattern | Implementation | Purpose |
|---------|----------------|---------|
| **Registry Pattern** | `agent_registry`, `team_registry`, `flow_registry` (implicit in directory structure) | Allows dynamic discovery and listing of available agents/teams/flows without hardcoding. |
| **Base Class Abstraction** | `BaseAgent`, `BaseTeam`, `BaseFlow` | Enforces a common interface for all entities, handling shared logic like session management, logging, and HITL state serialization. |
| **DTO Pattern** | `api/dto/*.py` | Separates the internal domain models from the external API contract using Pydantic models (Data Transfer Objects). |
| **Factory Pattern** | `config/llm_factory.py` | Centralizes the creation of LLM instances, abstracting away provider-specific initialization logic (OpenAI vs Anthropic vs Custom). |
| **Singleton Pattern** | `config/settings.py` (`get_settings`) | Ensures configuration is loaded once and cached for the application's lifetime. |
