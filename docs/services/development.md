# Development Guide

This guide covers how to set up your local development environment for the LlamaIndex Agents application, including both the backend (Python/FastAPI) and frontend (React/TypeScript).

## Prerequisites

-   **Python**: 3.12 or higher
-   **Node.js**: 20 or higher
-   **Docker**: For running PostgreSQL and Phoenix (Observability)
-   **uv**: Recommended Python package manager (faster than pip)

## 1. Backend Development (`agent/`)

The backend is built with FastAPI and LlamaIndex.

### Setup

1.  Navigate to the agent directory:
    ```bash
    cd agent
    ```

2.  Create a virtual environment and install dependencies (using `uv`):
    ```bash
    # Install dependencies from pyproject.toml
    uv sync
    ```
    *Alternatively, with standard pip:*
    ```bash
    python -m venv venv
    source venv/bin/activate
    pip install -e .
    ```

3.  Configure Environment Variables:
    Copy `.env.example` to `.env` in the root directory (or inside `agent/`):
    ```bash
    cp ../.env.example .env
    ```
    **Required Keys:**
    -   `OPENAI_API_KEY`: For LLM calls.
    -   `MEMORY_DATABASE_URI`: Database connection string.

### Database Setup

For local development, the easiest way to run the database is via Docker Compose, running only the required services:

```bash
# In the root directory
docker-compose up -d postgres phoenix
```

This starts:
-   PostgreSQL on port `5432`
-   Arize Phoenix on port `6006`

Ensure your `.env` points to localhost:
```properties
MEMORY_DATABASE_URI=postgresql+asyncpg://postgres:postgres@localhost:5432/llamaindex_agents
PHOENIX_ENDPOINT=http://localhost:6006
```

### Running the Server

Start the FastAPI development server with hot reload:

```bash
uv run uvicorn main:app --host 0.0.0.0 --port 6001 --reload
```
The API will be available at `http://localhost:6001`.
-   Docs: `http://localhost:6001/docs`

### Running Tests

We use `pytest` for testing.

```bash
# Run all tests
uv run pytest

# Run specific test file
uv run pytest tests/unit/test_agents.py
```

### Adding New Agents

1.  Create a new file in `agent/agents/` (e.g., `my_new_agent.py`).
2.  Inherit from `BaseAgent`.
3.  Implement `get_tools()` and define `NAME`, `DESCRIPTION`, and `DEFAULT_SYSTEM_PROMPT`.
4.  (Optional) Add it to `agent/api/v1/agent_controller.py` registry if you want it exposed via API (though the registry usually auto-discovers if imported).

## 2. Frontend Development (`agent-ui/`)

The frontend is a React application built with Vite and Tailwind CSS.

### Setup

1.  Navigate to the UI directory:
    ```bash
    cd agent-ui
    ```

2.  Install dependencies:
    ```bash
    npm install
    ```

### Running the Development Server

Start the Vite development server:

```bash
npm run dev
```

The app will run at `http://localhost:5173`.

**Note on Proxying:**
`vite.config.ts` is configured to proxy `/api` requests to `http://localhost:6001`. Ensure your backend is running on port 6001.

### Project Structure

-   `src/components/chat/`: Chat interface components.
-   `src/store/`: Redux state management (chat sessions, active agent).
-   `src/services/api.ts`: API client and SSE stream handling.

## 3. Full Stack with Docker Compose

To run the entire stack (Backend + Frontend + DB + Phoenix) exactly as it would look in production:

```bash
docker-compose up --build
```

-   Frontend: `http://localhost:3000`
-   Backend: `http://localhost:6001`
-   Phoenix: `http://localhost:6006`

*Note: This does not support hot-reloading for code changes unless you mount volumes, so strictly "local" development (steps 1 & 2) is preferred for active coding.*

## 4. Troubleshooting

**Database Connection Errors:**
-   Ensure the `postgres` container is running (`docker ps`).
-   Check `MEMORY_DATABASE_URI` matches the host/port (use `localhost` for local run, `postgres` for docker-compose run).

**LLM Errors:**
-   Check `OPENAI_API_KEY` is set.
-   If using a different provider, verify `LLM_PROVIDER` settings in `.env`.

**Linter Errors:**
-   Backend: Ensure you are using Python 3.12+.
-   Frontend: Run `npm run lint` to check for ESLint issues.

