# Observability & Monitoring

Observability is critical for building reliable agentic systems. Unlike traditional software, LLM applications require visibility into non-deterministic execution paths, prompt inputs/outputs, and tool usage.

This project integrates **Arize Phoenix**, an open-source observability platform designed for LLMs.

## Architecture

The observability stack consists of:

1.  **Instrumentation**: The backend uses `openinference-instrumentation-llama_index` to automatically hook into LlamaIndex internal events.
2.  **Collector**: Traces are sent to a local Phoenix server (running in Docker).
3.  **Visualization**: The Phoenix UI allows you to explore traces, view specific spans (LLM calls, tool execution), and debug latency or errors.

## Features

### 1. Full Execution Traces
Every interaction—whether a simple chat or a complex multi-agent workflow—is traced. You can see:
-   **Input/Output**: What the user said and what the agent replied.
-   **Reasoning**: The internal "thought process" (Chain-of-Thought) of the agent.
-   **Tool Calls**: Which tools were called, their arguments, and their return values.
-   **Latency**: How long each step took.

### 2. Multi-Agent Visualization
Phoenix visualizes the hierarchy of execution. For a `ResearchMathOrchestratorTeam`, you can clearly see the "Manager" span spawning child spans for the "Research Agent" and "Math Agent".

### 3. Error Tracking
If an agent fails (e.g., a tool raises an exception), the trace is marked as an error, allowing you to pinpoint exactly where the failure occurred.

## Configuration

Observability is configured in `agent/config/observability.py` and controlled via environment variables.

| Variable | Description | Default |
| :--- | :--- | :--- |
| `PHOENIX_ENABLED` | Master switch to enable/disable tracing. | `true` |
| `PHOENIX_ENDPOINT` | The URL of the Phoenix collector. | `http://localhost:6006` |
| `PHOENIX_PROJECT_NAME` | Group traces under this project name in the UI. | `llamaindex-agents` |
| `PHOENIX_BATCH_PROCESSOR` | `true` for async batching (prod), `false` for sync (dev). | `false` |

## Accessing the Dashboard

When running with Docker Compose, the Phoenix UI is available at:

**[http://localhost:6006](http://localhost:6006)**

### Usage Guide

1.  Open the dashboard.
2.  Go to the **Traces** tab.
3.  Select the project `llamaindex-agents`.
4.  Click on any trace ID to view the waterfall diagram of the execution.

## Production Considerations

-   **Batch Processing**: In production (`PHOENIX_BATCH_PROCESSOR=true`), traces are buffered and sent asynchronously to avoid slowing down the user request.
-   **Persistence**: The Docker Compose setup mounts a volume (`phoenix_data`) to persist traces across restarts.

