import type {
  Agent,
  AgentsResponse,
  Team,
  TeamsResponse,
  Flow,
  FlowsResponse,
  FlowRunStatus,
  ChatRequest,
  FlowRequest,
  HITLRespondRequest,
  StreamEvent,
  EntityType,
} from '../types';

const API_BASE = '/api/v1';

// ─────────────────────────────────────────────────────────────
// FETCH ENTITIES
// ─────────────────────────────────────────────────────────────

export async function fetchAgents(): Promise<Agent[]> {
  const response = await fetch(`${API_BASE}/agents`);
  if (!response.ok) {
    throw new Error(`Failed to fetch agents: ${response.statusText}`);
  }
  const data: AgentsResponse = await response.json();
  return data.agents;
}

export async function fetchTeams(): Promise<Team[]> {
  const response = await fetch(`${API_BASE}/teams`);
  if (!response.ok) {
    throw new Error(`Failed to fetch teams: ${response.statusText}`);
  }
  const data: TeamsResponse = await response.json();
  return data.teams;
}

export async function fetchFlows(): Promise<Flow[]> {
  const response = await fetch(`${API_BASE}/flows`);
  if (!response.ok) {
    throw new Error(`Failed to fetch flows: ${response.statusText}`);
  }
  const data: FlowsResponse = await response.json();
  return data.flows;
}

// ─────────────────────────────────────────────────────────────
// ASYNC FLOW EXECUTION (Polling-based)
// ─────────────────────────────────────────────────────────────

export async function startFlowAsync(
  flowId: string,
  request: FlowRequest
): Promise<{ run_id: string; status: string }> {
  const response = await fetch(`${API_BASE}/flows/${flowId}/run/async`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  });
  if (!response.ok) {
    const error = await response.text();
    throw new Error(`Failed to start flow: ${error || response.statusText}`);
  }
  return response.json();
}

export async function pollFlowRun(
  flowId: string,
  runId: string,
  includeSteps = true
): Promise<FlowRunStatus> {
  const url = `${API_BASE}/flows/${flowId}/run/${runId}?include_steps=${includeSteps}`;
  const response = await fetch(url);
  if (!response.ok) {
    const error = await response.text();
    throw new Error(`Failed to poll flow: ${error || response.statusText}`);
  }
  return response.json();
}

// ─────────────────────────────────────────────────────────────
// SSE PARSING
// ─────────────────────────────────────────────────────────────

function parseSSELine(line: string, eventType: string): StreamEvent | null {
  if (!line.startsWith('data:')) {
    return null;
  }

  const data = line.slice(5);
  const trimmedData = data.trim();

  if (trimmedData === '[DONE]') {
    return { type: 'done' };
  }

  if (trimmedData === '[HITL_PAUSE]') {
    return { type: 'hitl_pause' };
  }

  // Try to parse as JSON based on event type or content
  if (trimmedData.startsWith('{')) {
    try {
      const parsed = JSON.parse(trimmedData);

      // Handle named event types
      if (eventType === 'agent' && parsed.agent_name) {
        return {
          type: 'agent',
          agentName: parsed.agent_name,
        };
      }

      if (eventType === 'hitl' && parsed.workflow_id) {
        return {
          type: 'hitl',
          hitl: {
            workflowId: parsed.workflow_id,
            prompt: parsed.prompt,
            activeAgent: parsed.active_agent,
            sessionId: parsed.session_id,
          },
        };
      }

      // Flow events - check for flow-specific event types
      if (parsed.type) {
        const flowEventType = parsed.type as string;
        
        // StopEvent contains the final result
        if (flowEventType === 'StopEvent' && parsed.result) {
          return {
            type: 'flow_result',
            flowEvent: {
              eventType: flowEventType,
              data: parsed,
            },
          };
        }

        // Other flow events are progress updates
        return {
          type: 'flow_event',
          flowEvent: {
            eventType: flowEventType,
            data: parsed,
          },
        };
      }

      // Check if it's a HITL event without named event type
      if (parsed.workflow_id && parsed.prompt) {
        return {
          type: 'hitl',
          hitl: {
            workflowId: parsed.workflow_id,
            prompt: parsed.prompt,
            activeAgent: parsed.active_agent,
            sessionId: parsed.session_id,
          },
        };
      }

      // Check if it's an agent event without named event type
      if (parsed.agent_name) {
        return {
          type: 'agent',
          agentName: parsed.agent_name,
        };
      }
    } catch {
      // Not valid JSON, treat as regular token
    }
  }

  // Regular token
  const tokenData = data.startsWith(' ') ? data.slice(1) : data;
  return { type: 'token', data: tokenData };
}

// ─────────────────────────────────────────────────────────────
// STREAMING
// ─────────────────────────────────────────────────────────────

async function* streamFromEndpoint(
  endpoint: string,
  request: ChatRequest | FlowRequest | HITLRespondRequest,
  abortSignal?: AbortSignal
): AsyncGenerator<StreamEvent> {
  const response = await fetch(endpoint, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
    signal: abortSignal,
  });

  if (!response.ok) {
    throw new Error(`Request failed: ${response.statusText}`);
  }

  const reader = response.body?.getReader();
  if (!reader) {
    throw new Error('No response body');
  }

  const decoder = new TextDecoder();
  let buffer = '';
  let currentEventType = '';

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';

      for (const line of lines) {
        if (!line) continue;

        // Track event type for named events
        if (line.startsWith('event:')) {
          currentEventType = line.slice(6).trim();
          continue;
        }

        const event = parseSSELine(line, currentEventType);
        if (event) {
          yield event;
          currentEventType = '';
        }
      }
    }
  } finally {
    reader.releaseLock();
  }
}

// Agent streaming
export async function* streamAgentChat(
  agentId: string,
  request: ChatRequest,
  abortSignal?: AbortSignal
): AsyncGenerator<StreamEvent> {
  yield* streamFromEndpoint(
    `${API_BASE}/agents/${agentId}/chat/stream`,
    request,
    abortSignal
  );
}

// Team streaming
export async function* streamTeamChat(
  teamId: string,
  request: ChatRequest,
  abortSignal?: AbortSignal
): AsyncGenerator<StreamEvent> {
  yield* streamFromEndpoint(
    `${API_BASE}/teams/${teamId}/chat/stream`,
    request,
    abortSignal
  );
}

// Flow streaming
export async function* streamFlowRun(
  flowId: string,
  request: FlowRequest,
  abortSignal?: AbortSignal
): AsyncGenerator<StreamEvent> {
  yield* streamFromEndpoint(
    `${API_BASE}/flows/${flowId}/stream`,
    request,
    abortSignal
  );
}

// Generic stream that handles agents and teams (not flows in async mode)
export async function* streamChat(
  entityId: string,
  entityType: EntityType,
  message: string,
  sessionId?: string,
  abortSignal?: AbortSignal
): AsyncGenerator<StreamEvent> {
  if (entityType === 'flow') {
    yield* streamFlowRun(entityId, { topic: message, session_id: sessionId }, abortSignal);
  } else if (entityType === 'team') {
    yield* streamTeamChat(entityId, { message, session_id: sessionId }, abortSignal);
  } else {
    yield* streamAgentChat(entityId, { message, session_id: sessionId }, abortSignal);
  }
}

// ─────────────────────────────────────────────────────────────
// HITL RESPONSE
// ─────────────────────────────────────────────────────────────

export async function* streamAgentHITLResponse(
  agentId: string,
  request: HITLRespondRequest,
  abortSignal?: AbortSignal
): AsyncGenerator<StreamEvent> {
  yield* streamFromEndpoint(
    `${API_BASE}/agents/${agentId}/chat/stream/respond`,
    request,
    abortSignal
  );
}

export async function* streamTeamHITLResponse(
  teamId: string,
  request: HITLRespondRequest,
  abortSignal?: AbortSignal
): AsyncGenerator<StreamEvent> {
  yield* streamFromEndpoint(
    `${API_BASE}/teams/${teamId}/chat/stream/respond`,
    request,
    abortSignal
  );
}

export async function* streamFlowHITLResponse(
  flowId: string,
  request: HITLRespondRequest,
  abortSignal?: AbortSignal
): AsyncGenerator<StreamEvent> {
  const response = await fetch(`${API_BASE}/flows/${flowId}/run/respond`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
    signal: abortSignal,
  });

  if (!response.ok) {
    throw new Error(`Request failed: ${response.statusText}`);
  }

  const data = await response.json();
  
  if (data.status === 'pending_input') {
    yield {
      type: 'hitl',
      hitl: {
        workflowId: data.workflow_id,
        prompt: data.prompt,
        sessionId: data.session_id,
      },
    };
  } else {
    const resultText = typeof data.result === 'string' 
      ? data.result 
      : JSON.stringify(data.result, null, 2);
    yield { type: 'token', data: resultText };
    yield { type: 'done' };
  }
}

export async function* streamHITLResponse(
  entityId: string,
  entityType: EntityType,
  request: HITLRespondRequest,
  abortSignal?: AbortSignal
): AsyncGenerator<StreamEvent> {
  if (entityType === 'flow') {
    yield* streamFlowHITLResponse(entityId, request, abortSignal);
  } else if (entityType === 'team') {
    yield* streamTeamHITLResponse(entityId, request, abortSignal);
  } else {
    yield* streamAgentHITLResponse(entityId, request, abortSignal);
  }
}

// ─────────────────────────────────────────────────────────────
// SESSION MANAGEMENT
// ─────────────────────────────────────────────────────────────

export async function clearAgentSession(agentId: string, sessionId: string): Promise<void> {
  const response = await fetch(`${API_BASE}/agents/${agentId}/session/${sessionId}`, {
    method: 'DELETE',
  });
  if (!response.ok) {
    throw new Error(`Failed to clear session: ${response.statusText}`);
  }
}

export async function clearTeamSession(teamId: string, sessionId: string): Promise<void> {
  const response = await fetch(`${API_BASE}/teams/${teamId}/session/${sessionId}`, {
    method: 'DELETE',
  });
  if (!response.ok) {
    throw new Error(`Failed to clear session: ${response.statusText}`);
  }
}

export async function clearFlowSession(flowId: string, sessionId: string): Promise<void> {
  const response = await fetch(`${API_BASE}/flows/${flowId}/session/${sessionId}`, {
    method: 'DELETE',
  });
  if (!response.ok) {
    throw new Error(`Failed to clear session: ${response.statusText}`);
  }
}

export async function clearSession(
  entityId: string,
  entityType: EntityType,
  sessionId: string
): Promise<void> {
  if (entityType === 'flow') {
    await clearFlowSession(entityId, sessionId);
  } else if (entityType === 'team') {
    await clearTeamSession(entityId, sessionId);
  } else {
    await clearAgentSession(entityId, sessionId);
  }
}
