# Frontend UI Service

The Frontend service is a modern React application that provides an intuitive interface for interacting with the LlamaIndex Agents backend. It supports real-time chat, Markdown rendering, and dynamic handling of various agent types.

## Technology Stack

-   **Framework**: React 18
-   **Language**: TypeScript
-   **Build Tool**: Vite
-   **Styling**: Tailwind CSS
-   **State Management**: Redux Toolkit
-   **HTTP Client**: Native `fetch` API
-   **Routing**: None (currently a single-view app, but structure supports expansion)

## Directory Structure (`agent-ui/src/`)

-   `components/`: Reusable UI components.
    -   `chat/`: Chat-specific components (`ChatWindow`, `MessageBubble`, `ChatInput`).
    -   `layout/`: Layout components (`Sidebar`, `Header`).
-   `services/`: API integration logic (`api.ts`).
-   `store/`: Redux state slices (`chatSlice.ts`).
-   `hooks/`: Custom React hooks (`useChat.ts`).
-   `types/`: TypeScript interface definitions.
-   `App.tsx`: Main application component.
-   `main.tsx`: Entry point.

## Key Components

### Chat Interface
The core of the UI is the chat interface, which handles:
-   **Message Display**: Renders user and agent messages. Supports Markdown parsing for rich text output.
-   **Streaming**: Handles real-time text updates as tokens arrive from the backend.
-   **Input Handling**: Captures user input and handles submission states.

### Sidebar
Provides navigation and context switching between:
-   **Agents**: Individual agents available in the system.
-   **Teams**: Orchestrator teams.
-   **Flows**: Workflows.

### HITL Prompt
A specialized component (`HITLPrompt.tsx`) that appears when a workflow or agent requests human input. It allows the user to provide feedback or data mid-execution.

## State Management

The application uses **Redux Toolkit** for managing global state.

-   **`chatSlice`**: Manages the current chat session, including:
    -   `messages`: Array of chat messages.
    -   `isLoading`: Loading state.
    -   `activeSessionId`: Current session identifier.
    -   `selectedEntity`: The currently selected agent, team, or flow.

## API Integration

All API logic is encapsulated in `services/api.ts`.

-   **Fetching Entities**: Functions to get lists of agents, teams, and flows.
-   **Streaming**: Async generators (`streamChat`, `streamFlowRun`) that handle SSE parsing.
-   **SSE Parsing**: Custom logic to parse the `data:` lines from the SSE stream and convert them into typed events (`token`, `agent`, `hitl`, etc.).

## Development

To run the frontend locally:

```bash
cd agent-ui
# Install dependencies
npm install
# Start development server
npm run dev
```

The development server runs on `http://localhost:5173` by default and proxies API requests to `http://localhost:6001` (configured in `vite.config.ts`).

## Production Build

For production, the app is built into static files:

```bash
npm run build
```

The output in `dist/` is then served via Nginx (defined in `Dockerfile` and `nginx.conf`).

