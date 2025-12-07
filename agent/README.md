# LlamaIndex Agents

A FastAPI-based application for building and orchestrating AI agents using LlamaIndex.

## Concepts

### Agents

**Agents** are individual AI assistants with specific capabilities. Each agent has:
- A **name** and **description**
- A **system prompt** defining its personality/behavior
- A set of **tools** it can use to accomplish tasks
- **Memory** for maintaining conversation context

Agents use LLMs (like GPT-4) to reason about user queries and decide when to call tools. They support **Human-in-the-Loop (HITL)** for dangerous operations that require human confirmation.

**Examples:**
- `MathAgent` - Performs mathematical operations (add, multiply)
- `ResearchAgent` - Searches the web using Perplexity AI
- `MarketAgent` - Manages market index data (with HITL for updates)
- `WriterAgent` - Writes news articles with a journalistic style

### Teams

**Teams** are multi-agent orchestrations using LlamaIndex's `AgentWorkflow`. They coordinate multiple agents to solve complex tasks. Teams support two patterns:

1. **Handoff Pattern**: Agents can hand off conversations to other agents based on expertise
2. **Orchestrator Pattern**: A central agent delegates tasks to specialized agents as tools

Teams have:
- A **root agent** that receives initial queries
- **Shared memory** across all agents in the team
- **Handoff rules** defining which agents can delegate to others

**Examples:**
- `MarketResearchTeam` - Research + Market agents with bidirectional handoffs
- `ResearchMathOrchestratorTeam` - Orchestrator that delegates to Research and Math agents

### Flows

**Flows** are event-driven pipelines using LlamaIndex's `Workflow` system. Unlike teams (which are conversation-based), flows are designed for structured, multi-step processes with explicit data flow between steps.

Flows have:
- **Steps** decorated with `@step` that process events
- **Custom events** for passing data between steps
- Support for **branching** and **looping** logic
- **Database logging** for tracking execution status

**Examples:**
- `StoryFlow` - Research a topic → Write an article
- `StoryCriticFlow` - Research → Write → Critique → Rewrite (with max 3 attempts)

## Project Structure

```
agent/
├── agents/                 # Individual AI agents
│   ├── __init__.py         # Agent registry
│   ├── base.py             # BaseAgent abstract class
│   ├── math_agent.py       # Mathematical operations
│   ├── research_agent.py   # Web search via Perplexity
│   ├── market_agent.py     # Market data with HITL
│   ├── writer_agent.py     # Article writing
│   └── critic_agent.py     # Article critique
│
├── teams/                  # Multi-agent teams
│   ├── __init__.py         # Team registry
│   ├── base.py             # BaseTeam abstract class
│   ├── market_research_team.py
│   └── research_math_orchestrator_team.py
│
├── flows/                  # Event-driven workflows
│   ├── __init__.py         # Flow registry
│   ├── base.py             # BaseFlow abstract class
│   ├── story_flow.py       # Research → Write pipeline
│   └── story_critic_flow.py # With critique loop
│
├── tools/                  # Agent tools
│   ├── math_tools.py       # add, multiply
│   ├── research_tools.py   # web_search (Perplexity)
│   └── market_tools.py     # get_index, push_index (HITL)
│
├── api/                    # FastAPI endpoints
│   ├── __init__.py
│   ├── dto/                # Request/Response models
│   │   ├── agent_dto.py
│   │   ├── team_dto.py
│   │   └── flow_dto.py
│   └── v1/
│       ├── agent_controller.py
│       ├── team_controller.py
│       └── flow_controller.py
│
├── config/                 # Configuration
│   ├── settings.py         # Pydantic Settings
│   ├── database.py         # DB manager (memory, workflow states)
│   └── observability.py    # Arize Phoenix tracing
│
├── tests/                  # Unit and API tests
│   ├── conftest.py         # Shared fixtures
│   ├── unit/
│   └── api/
│
├── main.py                 # FastAPI app entry point
├── pyproject.toml          # Dependencies
└── .env                    # Environment variables (not in git)
```

## Setup

### Prerequisites

- Python 3.12+
- [uv](https://github.com/astral-sh/uv) package manager
- PostgreSQL (optional, for persistent memory)
- Arize Phoenix (optional, for observability)

### Installation

```bash
# Clone and navigate to project
cd agent

# Install dependencies
uv sync

# Install with test dependencies
uv sync --extra test
```

### Environment Variables

Create a `.env` file:

```bash
# Required
OPENAI_API_KEY=your-openai-api-key
OPENAI_API_BASE=https://api.openai.com/v1

# Optional: LLM settings
DEFAULT_MODEL=gpt-4.1-nano
DEFAULT_TEMPERATURE=0.0

# Optional: Perplexity (for ResearchAgent)
PERPLEXITY_API_KEY=your-perplexity-api-key
PERPLEXITY_API_BASE_URL=https://api.perplexity.ai
PERPLEXITY_MODEL=sonar

# Optional: PostgreSQL for persistent memory
MEMORY_DATABASE_URI=postgresql+asyncpg://user:pass@localhost:5432/dbname

# Optional: Arize Phoenix observability
PHOENIX_ENABLED=true
PHOENIX_ENDPOINT=http://localhost:6006
PHOENIX_PROJECT_NAME=llamaindex-agents
```

## Running the API

### Development

```bash
# Start the server
uv run uvicorn main:app --reload --port 6001

# Or use Python directly
uv run python main.py
```

The API will be available at `http://localhost:6001`.

### API Documentation

- Swagger UI: `http://localhost:6001/docs`
- ReDoc: `http://localhost:6001/redoc`

## API Endpoints

### Health Check

```
GET /health
```

### Agents

```
GET  /api/v1/agents                          # List all agents
POST /api/v1/agents/{id}/chat                # Chat (JSON response)
POST /api/v1/agents/{id}/chat/stream         # Chat (SSE stream)
POST /api/v1/agents/{id}/chat/respond        # Resume HITL (JSON)
POST /api/v1/agents/{id}/chat/stream/respond # Resume HITL (SSE)
DELETE /api/v1/agents/{id}/session/{sid}     # Clear session memory
```

### Teams

```
GET  /api/v1/teams                           # List all teams
POST /api/v1/teams/{name}/chat               # Chat (JSON response)
POST /api/v1/teams/{name}/chat/stream        # Chat (SSE stream)
POST /api/v1/teams/{name}/chat/respond       # Resume HITL (JSON)
POST /api/v1/teams/{name}/chat/stream/respond # Resume HITL (SSE)
DELETE /api/v1/teams/{name}/session/{sid}    # Clear session memory
```

### Flows

```
GET  /api/v1/flows                           # List all flows
POST /api/v1/flows/{id}/run                  # Run (sync, with DB logging)
POST /api/v1/flows/{id}/run/respond          # Resume HITL
POST /api/v1/flows/{id}/run/async            # Run async (returns run_id)
GET  /api/v1/flows/{id}/run/{run_id}         # Poll run status
GET  /api/v1/flows/{id}/run/{run_id}/steps   # Get step details
POST /api/v1/flows/{id}/stream               # Stream events (SSE)
DELETE /api/v1/flows/{id}/session/{sid}      # Clear session memory
```

## Usage Examples

### Chat with an Agent

```bash
curl -X POST http://localhost:6001/api/v1/agents/math/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What is 5 + 3?", "session_id": "user123"}'
```

### Stream from a Team

```bash
curl -X POST http://localhost:6001/api/v1/teams/market_research_team/chat/stream \
  -H "Content-Type: application/json" \
  -d '{"message": "Research the current NIFTY index", "session_id": "user123"}'
```

### Run a Flow Asynchronously

```bash
# Start the flow
curl -X POST http://localhost:6001/api/v1/flows/story_flow/run/async \
  -H "Content-Type: application/json" \
  -d '{"topic": "AI in healthcare"}'

# Poll for status
curl http://localhost:6001/api/v1/flows/story_flow/run/{run_id}
```

## Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=.

# Run specific test file
uv run pytest tests/unit/test_tools.py
```

## Linting and Formatting

```bash
# Check for issues
uv run ruff check .

# Auto-format
uv run ruff format .
```

## License

MIT

