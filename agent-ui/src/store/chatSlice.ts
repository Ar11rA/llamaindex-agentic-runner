import { createSlice, createAsyncThunk, type PayloadAction } from '@reduxjs/toolkit';
import { v4 as uuidv4 } from 'uuid';
import type { Conversation, Message, HITLState, ChatState, EntityType, FlowMode } from '../types';
import {
  fetchAgents as fetchAgentsApi,
  fetchTeams as fetchTeamsApi,
  fetchFlows as fetchFlowsApi,
} from '../services/api';

// Load conversations from localStorage
function loadConversations(): Conversation[] {
  try {
    const stored = localStorage.getItem('agent-ui-conversations');
    return stored ? JSON.parse(stored) : [];
  } catch {
    return [];
  }
}

// Save conversations to localStorage
function saveConversations(conversations: Conversation[]) {
  localStorage.setItem('agent-ui-conversations', JSON.stringify(conversations));
}

const initialState: ChatState = {
  conversations: loadConversations(),
  activeConversationId: null,
  agents: [],
  teams: [],
  flows: [],
  selectedEntityId: null,
  selectedEntityType: 'agent',
  flowMode: 'stream',
  isLoading: false,
  isStreaming: false,
  hitlState: null,
  currentAgentName: null,
  abortController: null,
  error: null,
};

// Async thunks
export const fetchAgents = createAsyncThunk('chat/fetchAgents', async () => {
  const agents = await fetchAgentsApi();
  return agents;
});

export const fetchTeams = createAsyncThunk('chat/fetchTeams', async () => {
  const teams = await fetchTeamsApi();
  return teams;
});

export const fetchFlows = createAsyncThunk('chat/fetchFlows', async () => {
  const flows = await fetchFlowsApi();
  return flows;
});

const chatSlice = createSlice({
  name: 'chat',
  initialState,
  reducers: {
    // Set entity type (agent, team, or flow)
    setEntityType(state, action: PayloadAction<EntityType>) {
      state.selectedEntityType = action.payload;
      state.selectedEntityId = null;
      state.activeConversationId = null;
    },

    // Select an entity
    selectEntity(state, action: PayloadAction<string>) {
      state.selectedEntityId = action.payload;
    },

    // Set flow execution mode
    setFlowMode(state, action: PayloadAction<FlowMode>) {
      state.flowMode = action.payload;
    },

    // Create a new conversation
    createConversation(state, action: PayloadAction<{ entityId: string; entityType: EntityType }>) {
      const { entityId, entityType } = action.payload;

      // Find the entity name
      let entityName = entityId;
      if (entityType === 'agent') {
        const agent = state.agents.find((a) => a.id === entityId);
        entityName = agent?.name || entityId;
      } else if (entityType === 'team') {
        const team = state.teams.find((t) => t.id === entityId);
        entityName = team?.name || entityId;
      } else {
        const flow = state.flows.find((f) => f.id === entityId);
        entityName = flow?.name || entityId;
      }

      const conversation: Conversation = {
        id: uuidv4(),
        sessionId: uuidv4(),
        entityId,
        entityType,
        title: `${entityType === 'flow' ? 'Run' : 'Chat with'} ${entityName}`,
        messages: [],
        createdAt: Date.now(),
        updatedAt: Date.now(),
      };
      state.conversations.unshift(conversation);
      state.activeConversationId = conversation.id;
      saveConversations(state.conversations);
    },

    // Set active conversation
    setActiveConversation(state, action: PayloadAction<string | null>) {
      state.activeConversationId = action.payload;
      if (action.payload) {
        const conversation = state.conversations.find((c) => c.id === action.payload);
        if (conversation) {
          state.selectedEntityId = conversation.entityId;
          state.selectedEntityType = conversation.entityType;
        }
      }
    },

    // Delete a conversation
    deleteConversation(state, action: PayloadAction<string>) {
      const index = state.conversations.findIndex((c) => c.id === action.payload);
      if (index !== -1) {
        state.conversations.splice(index, 1);
        if (state.activeConversationId === action.payload) {
          state.activeConversationId = state.conversations[0]?.id || null;
        }
        saveConversations(state.conversations);
      }
    },

    // Add a user message
    addUserMessage(state, action: PayloadAction<{ conversationId: string; content: string }>) {
      const { conversationId, content } = action.payload;
      const conversation = state.conversations.find((c) => c.id === conversationId);
      if (conversation) {
        const message: Message = {
          id: uuidv4(),
          role: 'user',
          content,
          timestamp: Date.now(),
        };
        conversation.messages.push(message);
        conversation.updatedAt = Date.now();
        // Update title if this is the first message
        if (conversation.messages.length === 1) {
          conversation.title = content.slice(0, 50) + (content.length > 50 ? '...' : '');
        }
        saveConversations(state.conversations);
      }
    },

    // Start assistant message (streaming)
    startAssistantMessage(state, action: PayloadAction<{ conversationId: string }>) {
      const { conversationId } = action.payload;
      const conversation = state.conversations.find((c) => c.id === conversationId);
      if (conversation) {
        const message: Message = {
          id: uuidv4(),
          role: 'assistant',
          content: '',
          timestamp: Date.now(),
          isStreaming: true,
        };
        conversation.messages.push(message);
        state.isStreaming = true;
        state.currentAgentName = null;
      }
    },

    // Set current agent name
    setCurrentAgentName(state, action: PayloadAction<string | null>) {
      state.currentAgentName = action.payload;
      if (state.activeConversationId && action.payload) {
        const conversation = state.conversations.find((c) => c.id === state.activeConversationId);
        if (conversation) {
          const lastMessage = conversation.messages[conversation.messages.length - 1];
          if (lastMessage && lastMessage.role === 'assistant') {
            lastMessage.agentName = action.payload;
          }
        }
      }
    },

    // Append to assistant message (streaming)
    appendToAssistantMessage(state, action: PayloadAction<{ conversationId: string; content: string }>) {
      const { conversationId, content } = action.payload;
      const conversation = state.conversations.find((c) => c.id === conversationId);
      if (conversation) {
        const lastMessage = conversation.messages[conversation.messages.length - 1];
        if (lastMessage && lastMessage.role === 'assistant' && lastMessage.isStreaming) {
          lastMessage.content += content;
        }
      }
    },

    // Complete assistant message
    completeAssistantMessage(state, action: PayloadAction<{ conversationId: string }>) {
      const { conversationId } = action.payload;
      const conversation = state.conversations.find((c) => c.id === conversationId);
      if (conversation) {
        const lastMessage = conversation.messages[conversation.messages.length - 1];
        if (lastMessage && lastMessage.role === 'assistant') {
          lastMessage.isStreaming = false;
        }
        conversation.updatedAt = Date.now();
        state.isStreaming = false;
        saveConversations(state.conversations);
      }
    },

    // Cancel streaming
    cancelStreaming(state) {
      state.isStreaming = false;
      state.hitlState = null;
      state.currentAgentName = null;
      if (state.activeConversationId) {
        const conversation = state.conversations.find((c) => c.id === state.activeConversationId);
        if (conversation) {
          const lastMessage = conversation.messages[conversation.messages.length - 1];
          if (lastMessage && lastMessage.role === 'assistant' && lastMessage.isStreaming) {
            lastMessage.isStreaming = false;
            lastMessage.content += ' [Cancelled]';
          }
          saveConversations(state.conversations);
        }
      }
    },

    // Set HITL state
    setHITLState(state, action: PayloadAction<HITLState | null>) {
      state.hitlState = action.payload;
    },

    // Set loading state
    setLoading(state, action: PayloadAction<boolean>) {
      state.isLoading = action.payload;
    },

    // Set error
    setError(state, action: PayloadAction<string | null>) {
      state.error = action.payload;
    },

    // Clear error
    clearError(state) {
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      // Agents
      .addCase(fetchAgents.pending, (state) => {
        state.isLoading = true;
      })
      .addCase(fetchAgents.fulfilled, (state, action) => {
        state.agents = action.payload;
        state.isLoading = false;
        if (!state.selectedEntityId && state.selectedEntityType === 'agent' && action.payload.length > 0) {
          state.selectedEntityId = action.payload[0].id;
        }
      })
      .addCase(fetchAgents.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.error.message || 'Failed to fetch agents';
      })
      // Teams
      .addCase(fetchTeams.pending, (state) => {
        state.isLoading = true;
      })
      .addCase(fetchTeams.fulfilled, (state, action) => {
        state.teams = action.payload;
        state.isLoading = false;
      })
      .addCase(fetchTeams.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.error.message || 'Failed to fetch teams';
      })
      // Flows
      .addCase(fetchFlows.pending, (state) => {
        state.isLoading = true;
      })
      .addCase(fetchFlows.fulfilled, (state, action) => {
        state.flows = action.payload;
        state.isLoading = false;
      })
      .addCase(fetchFlows.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.error.message || 'Failed to fetch flows';
      });
  },
});

export const {
  setEntityType,
  selectEntity,
  setFlowMode,
  createConversation,
  setActiveConversation,
  deleteConversation,
  addUserMessage,
  startAssistantMessage,
  setCurrentAgentName,
  appendToAssistantMessage,
  completeAssistantMessage,
  cancelStreaming,
  setHITLState,
  setLoading,
  setError,
  clearError,
} = chatSlice.actions;

export default chatSlice.reducer;
