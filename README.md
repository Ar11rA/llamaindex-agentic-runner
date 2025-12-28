# LlamaIndex Agents

A full-stack application for building and interacting with LLM-powered agents, teams, and flows using LlamaIndex.

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│    Frontend     │────▶│     Backend     │────▶│    Phoenix      │
│   (React UI)    │     │    (FastAPI)    │     │  (Observability)│
│   Port: 3000    │     │   Port: 6001    │     │   Port: 6006    │
└─────────────────┘     └────────┬────────┘     └─────────────────┘
                                 │
                                 ▼
                        ┌─────────────────┐
                        │   PostgreSQL    │
                        │  (Memory Store) │
                        │   Port: 5432    │
                        └─────────────────┘
```

## Documentation

This repository contains comprehensive documentation for all aspects of the system:

-   **[Architecture Overview](docs/arch/architecture.md)**: High-level system design, service interaction, and software patterns.
-   **[Agentic Patterns](docs/arch/agentic_patterns.md)**: Deep dive into Single Agents, Multi-Agent Teams (Handoff/Orchestrator), and Event-Driven Flows.
-   **[Backend API Service](docs/services/backend_api.md)**: API endpoints, code structure, and configuration.
-   **[Frontend UI Service](docs/services/ui.md)**: React app structure, state management, and API integration.
-   **[Development Guide](docs/services/development.md)**: Setup guide for local backend and frontend development.
-   **[Testing Guide](docs/services/testing.md)**: Unit testing strategy and manual testing scenarios.
-   **[Deployment Guide](docs/services/deployment.md)**: Docker build process, Nginx configuration, and production setup.
-   **[Observability](docs/arch/observability.md)**: Monitoring and tracing with Arize Phoenix.

## Features

- **Single Agents** - Individual LlamaIndex agents with tool access
- **Teams** - Multi-agent orchestration with handoffs (AgentWorkflow)
- **Flows** - Event-driven workflows with step-by-step execution
- **Streaming** - Real-time SSE streaming for all interactions
- **HITL** - Human-in-the-loop support for agent/team decisions
- **Observability** - Full trace visibility via Phoenix UI

## Quick Start

### Using Docker Compose (Recommended)

1. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

2. **Start all services:**
   ```bash
   docker-compose up -d
   ```

3. **Access the application:**
   - Frontend: http://localhost:3000
   - Phoenix UI: http://localhost:6006
   - Backend API: http://localhost:6001

### Local Development

#### Backend

```bash
cd agent
uv sync
cp .env.example .env
# Edit .env with your API keys
uv run uvicorn main:app --reload --port 6001
```

#### Frontend

```bash
cd agent-ui
npm install
npm run dev
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENAI_API_KEY` | Yes | OpenAI API key |
| `OPENAI_API_BASE` | Yes | OpenAI API base URL |
| `PERPLEXITY_API_KEY` | No | Perplexity API key for web search |
| `PERPLEXITY_API_BASE_URL` | No | Perplexity API base URL |
| `PHOENIX_ENABLED` | No | Enable Phoenix tracing (default: true) |
| `PHOENIX_ENDPOINT` | No | Phoenix collector endpoint |
| `MEMORY_DATABASE_URI` | No | PostgreSQL connection string |

## Agentic Capabilities

This repository serves as a reference implementation for LlamaIndex's agentic framework. For detailed explanations, see **[Agentic Patterns](docs/arch/agentic_patterns.md)**.

We implement three core patterns:
1.  **Single Agents (ReAct)**: Tool-using agents (Math, Research, Market).
2.  **Multi-Agent Teams**:
    -   **Handoff**: Agents passing control to peers.
    -   **Orchestrator**: A manager agent delegating tasks to sub-agents.
3.  **Event-Driven Flows**: State machines with branching, looping, and human intervention (e.g., Story Critic Flow).

## Known Issues & Limitations

### LLM Provider Compatibility

The application supports multiple LLM providers via a factory pattern, but not all providers work with all features:

| Provider | Tool-Using Agents | Toolless Agents | Notes |
|----------|-------------------|-----------------|-------|
| **OpenAI** | ✅ Full support | ✅ Full support | Recommended for agents with tools |
| **Anthropic** | ❌ Broken | ✅ Works | `ToolCallBlock` not supported in LlamaIndex adapter |
| **Gemini Vertex** | ❌ Not implemented | ✅ Works | Custom LLM doesn't implement tool interface |
| **Bedrock Gateway** | ❌ Not implemented | ✅ Works | Custom LLM doesn't implement tool interface |

**Recommendation**: Use **OpenAI** as the default provider for full compatibility.

## License

MIT
