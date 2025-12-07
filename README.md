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

## License

MIT

