// Agent types
export interface Agent {
  id: string;
  name: string;
  description?: string;
}

export interface AgentsResponse {
  agents: Agent[];
}

// Team types (multi-agent teams)
export interface Team {
  id: string;
  name: string;
  description?: string;
}

export interface TeamsResponse {
  teams: Team[];
}

// Flow types (event-driven flows)
export interface Flow {
  id: string;
  name: string;
  description?: string;
}

export interface FlowsResponse {
  flows: Flow[];
}

// Entity type (agent, team, or flow)
export type EntityType = 'agent' | 'team' | 'flow';

// Flow execution mode
export type FlowMode = 'stream' | 'async';

// Flow run status (for async polling)
export interface FlowRunStatus {
  run_id: string;
  flow_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  input_data?: Record<string, unknown>;
  result?: unknown;
  error?: string;
  started_at?: string;
  completed_at?: string;
  metadata?: Record<string, unknown>;
  steps?: FlowStepStatus[];
}

export interface FlowStepStatus {
  id: string;
  step_name: string;
  step_index: number;
  status: string;
  event_type?: string;
  event_data?: Record<string, unknown>;
  started_at?: string;
  completed_at?: string;
  duration_ms?: number;
}

// Message types
export interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: number;
  isStreaming?: boolean;
  agentName?: string; // Name of the agent that generated this message
}

// Conversation types
export interface Conversation {
  id: string;
  sessionId: string;
  entityId: string; // agent, team, or flow ID
  entityType: EntityType;
  title: string;
  messages: Message[];
  createdAt: number;
  updatedAt: number;
}

// Chat request/response types (for agents and teams)
export interface ChatRequest {
  message: string;
  session_id?: string;
}

// Flow request (uses topic instead of message)
export interface FlowRequest {
  topic: string;
  session_id?: string;
}

export interface ChatResponse {
  status: 'completed';
  response: string;
  session_id?: string;
  responding_agents?: string[];
}

export interface FlowResponse {
  status: 'completed';
  result: unknown;
  session_id?: string;
}

export interface HITLPendingResponse {
  status: 'pending_input';
  workflow_id: string;
  prompt: string;
  active_agent?: string;
  session_id?: string;
}

export interface HITLRespondRequest {
  workflow_id: string;
  response: string;
}

// HITL state for UI
export interface HITLState {
  workflowId: string;
  prompt: string;
  activeAgent?: string;
  sessionId?: string;
}

// Stream event types
export type StreamEventType = 'token' | 'hitl' | 'done' | 'hitl_pause' | 'error' | 'agent' | 'flow_event' | 'flow_result';

export interface StreamEvent {
  type: StreamEventType;
  data?: string;
  hitl?: HITLState;
  agentName?: string; // For agent change events
  flowEvent?: {
    eventType: string;
    data: Record<string, unknown>;
  };
}

// Chat state
export interface ChatState {
  conversations: Conversation[];
  activeConversationId: string | null;
  agents: Agent[];
  teams: Team[];
  flows: Flow[];
  selectedEntityId: string | null;
  selectedEntityType: EntityType;
  flowMode: FlowMode;
  isLoading: boolean;
  isStreaming: boolean;
  hitlState: HITLState | null;
  currentAgentName: string | null; // Track which agent is currently responding
  abortController: AbortController | null;
  error: string | null;
}
