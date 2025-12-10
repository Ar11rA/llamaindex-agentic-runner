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

### Components

| Component | Description |
|-----------|-------------|
| **agent/** | Python backend with FastAPI, LlamaIndex agents, teams, and flows |
| **agent-ui/** | React frontend with chat interface, Redux state management |
| **Phoenix** | Arize Phoenix for LLM observability and tracing |
| **PostgreSQL** | Database for conversation memory persistence |

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

# Install dependencies with uv
uv sync

# Create .env file
cp .env.example .env
# Edit .env with your API keys

# Run the server
uv run uvicorn main:app --reload --port 6001
```

#### Frontend

```bash
cd agent-ui

# Install dependencies
npm install

# Run development server
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

## API Endpoints

### Agents (`/api/v1/agents`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | List available agents |
| POST | `/{agent_id}/chat` | Send message (non-streaming) |
| POST | `/{agent_id}/stream` | Send message (SSE streaming) |
| POST | `/{agent_id}/respond` | Respond to HITL prompt |
| DELETE | `/{agent_id}/session` | Clear session memory |

### Teams (`/api/v1/teams`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | List available teams |
| POST | `/{team_id}/chat` | Send message (non-streaming) |
| POST | `/{team_id}/stream` | Send message (SSE streaming) |
| POST | `/{team_id}/respond` | Respond to HITL prompt |
| DELETE | `/{team_id}/session` | Clear session memory |

### Flows (`/api/v1/flows`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | List available flows |
| POST | `/{flow_id}/run` | Run flow synchronously |
| POST | `/{flow_id}/run/async` | Start flow asynchronously |
| GET | `/{flow_id}/run/{run_id}` | Poll async flow status |
| GET | `/{flow_id}/run/{run_id}/steps` | Get flow execution steps |
| POST | `/{flow_id}/stream` | Run flow with SSE streaming |
| DELETE | `/{flow_id}/session` | Clear session |

## GenAI & Agentic Concepts

This repository serves as a **reference implementation** covering major patterns in LlamaIndex's agentic framework.

### Core Agentic Patterns

#### 1. Single Agents (ReAct Pattern)
Tool-equipped agents that can reason and act using external tools:
- `MathAgent` - Mathematical operations
- `ResearchAgent` - Web search via Perplexity
- `MarketAgent` - Market data with HITL protection
- `WriterAgent` / `CriticAgent` - Content generation and review

#### 2. Multi-Agent Teams
Two coordination patterns implemented:

| Pattern | Example | How It Works |
|---------|---------|--------------|
| **Handoff** | `MarketResearchTeam` | Agents use `can_handoff_to` to pass control dynamically |
| **Orchestrator** | `ResearchMathOrchestratorTeam` | Central agent uses specialized agents as tools (`agent.as_tool()`) |

#### 3. Event-Driven Flows
Step-based execution with `@step` decorators and event routing:
- `StoryCriticFlow` demonstrates **branching & looping**:
  - Research → Write → Critique
  - If rejected: loop back to rewrite (max 3 attempts)
  - If approved: return final article

### Tool Integration

| Tool | Implementation | Purpose |
|------|----------------|---------|
| Math tools | `add()`, `multiply()` | Simple function tools |
| Market tools | `get_index()`, `push_index()` | HITL-protected dangerous operations |
| Web search | `web_search()` via Perplexity | External LLM as a tool |

### Advanced Concepts

| Concept | Description |
|---------|-------------|
| **Human-in-the-Loop (HITL)** | Pause workflows for human approval, serialize/restore context |
| **Streaming (SSE)** | Real-time token streaming with `AgentStream` events |
| **Memory Persistence** | Per-session conversation history in PostgreSQL |
| **Async Execution** | Fire-and-forget flows with status polling API |
| **Observability** | OpenTelemetry + Phoenix for full LLM trace visibility |

### Architecture Patterns

| Pattern | Implementation |
|---------|----------------|
| Registry Pattern | `agent_registry`, `team_registry`, `flow_registry` |
| Base Class Abstraction | `BaseAgent`, `BaseTeam`, `BaseFlow` with shared behaviors |
| DTO Pattern | Separate request/response schemas in `api/dto/` |
| Session Management | Session IDs for memory isolation |

## Project Structure

```
llamaindex-agents/
├── agent/                    # Backend
│   ├── agents/              # Single agent definitions
│   ├── teams/               # Multi-agent teams
│   ├── flows/               # Event-driven workflows
│   ├── tools/               # Agent tools (math, research, etc.)
│   ├── api/                 # FastAPI routes and DTOs
│   ├── config/              # Settings, database, observability
│   └── main.py              # Application entry point
├── agent-ui/                # Frontend
│   ├── src/
│   │   ├── components/      # React components
│   │   ├── hooks/           # Custom hooks (useChat)
│   │   ├── services/        # API client
│   │   ├── store/           # Redux state
│   │   └── types/           # TypeScript interfaces
│   └── nginx.conf           # Production nginx config
├── docker-compose.yml       # Multi-service orchestration
└── .env.example             # Environment template
```

## Known Issues & Limitations

### LLM Provider Compatibility

The application supports multiple LLM providers via a factory pattern, but not all providers work with all features:

| Provider | Tool-Using Agents | Toolless Agents | Notes |
|----------|-------------------|-----------------|-------|
| **OpenAI** | ✅ Full support | ✅ Full support | Recommended for agents with tools |
| **Anthropic** | ❌ Broken | ✅ Works | `ToolCallBlock` not supported in LlamaIndex adapter |
| **Gemini Vertex** | ❌ Not implemented | ✅ Works | Custom LLM doesn't implement tool interface |
| **Bedrock Gateway** | ❌ Not implemented | ✅ Works | Custom LLM doesn't implement tool interface |
| **Cohere** | ⚠️ Untested | ⚠️ Untested | Base URL parameter may not work correctly |

**Tool-using agents:** `MathAgent`, `ResearchAgent`, `MarketAgent`  
**Toolless agents:** `WriterAgent`, `CriticAgent`

### Specific Issues

1. **Anthropic + Tools**
   - Error: `ValueError: Unsupported block type: <class 'llama_index.core.base.llms.types.ToolCallBlock'>`
   - Cause: LlamaIndex's Anthropic adapter doesn't handle `FunctionAgent`'s tool call format
   - Workaround: Use OpenAI for agents with tools

2. **Custom LLMs (GeminiVertexLLM, BedrockGatewayLLM)**
   - These implement basic `chat`/`complete` methods only
   - Tool calling requires `FunctionCallingLLM` interface which is not implemented
   - Use for toolless agents or flows only

3. **Cohere Base URL**
   - The `api_url` parameter may not be honored by LlamaIndex's Cohere adapter
   - Standard Cohere API endpoint works; custom gateways untested

### Recommendations

- Use **OpenAI** as the default provider for full compatibility
- Switch individual toolless agents to other providers via `provider=LLMProvider.X` parameter
- Set `LLM_PROVIDER` environment variable to change the global default

## License

MIT

