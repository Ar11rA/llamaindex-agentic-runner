import { useAppDispatch, useAppSelector } from '../../store';
import {
  setEntityType,
  selectEntity,
  setFlowMode,
  createConversation,
  setActiveConversation,
  deleteConversation,
} from '../../store/chatSlice';
import type { EntityType, FlowMode } from '../../types';

export function Sidebar() {
  const dispatch = useAppDispatch();
  const {
    agents,
    teams,
    flows,
    selectedEntityId,
    selectedEntityType,
    flowMode,
    conversations,
    activeConversationId,
    isStreaming,
  } = useAppSelector((state) => state.chat);

  // Get entities based on selected type
  const entities = 
    selectedEntityType === 'agent' ? agents : 
    selectedEntityType === 'team' ? teams : 
    flows;

  const handleEntityTypeChange = (type: EntityType) => {
    if (isStreaming) return;
    dispatch(setEntityType(type));
  };

  const handleFlowModeChange = (mode: FlowMode) => {
    if (isStreaming) return;
    dispatch(setFlowMode(mode));
  };

  const handleNewChat = () => {
    if (!selectedEntityId) return;
    dispatch(createConversation({ entityId: selectedEntityId, entityType: selectedEntityType }));
  };

  const handleSelectConversation = (id: string) => {
    if (isStreaming) return;
    dispatch(setActiveConversation(id));
  };

  const handleDeleteConversation = (e: React.MouseEvent, id: string) => {
    e.stopPropagation();
    dispatch(deleteConversation(id));
  };

  // Filter conversations for the selected entity type and entity
  const filteredConversations = conversations.filter(
    (c) => c.entityType === selectedEntityType && c.entityId === selectedEntityId
  );

  // Get label based on entity type
  const getEntityLabel = () => {
    switch (selectedEntityType) {
      case 'agent': return 'Agent';
      case 'team': return 'Team';
      case 'flow': return 'Flow';
    }
  };

  const getEntityPlaceholder = () => {
    switch (selectedEntityType) {
      case 'agent': return 'an agent';
      case 'team': return 'a team';
      case 'flow': return 'a flow';
    }
  };

  return (
    <aside className="w-72 bg-[var(--color-navy-900)] border-r border-[var(--color-navy-700)] flex flex-col h-full">
      {/* Entity Type Tabs */}
      <div className="p-3 border-b border-[var(--color-navy-700)]">
        <div className="flex bg-[var(--color-navy-800)] rounded-lg p-1">
          <button
            onClick={() => handleEntityTypeChange('agent')}
            disabled={isStreaming}
            className={`flex-1 px-2 py-2 text-xs font-medium rounded-md transition-all ${
              selectedEntityType === 'agent'
                ? 'bg-[var(--color-royal-600)] text-white'
                : 'text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)]'
            } disabled:opacity-50`}
          >
            Agents
          </button>
          <button
            onClick={() => handleEntityTypeChange('team')}
            disabled={isStreaming}
            className={`flex-1 px-2 py-2 text-xs font-medium rounded-md transition-all ${
              selectedEntityType === 'team'
                ? 'bg-[var(--color-royal-600)] text-white'
                : 'text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)]'
            } disabled:opacity-50`}
          >
            Teams
          </button>
          <button
            onClick={() => handleEntityTypeChange('flow')}
            disabled={isStreaming}
            className={`flex-1 px-2 py-2 text-xs font-medium rounded-md transition-all ${
              selectedEntityType === 'flow'
                ? 'bg-[var(--color-royal-600)] text-white'
                : 'text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)]'
            } disabled:opacity-50`}
          >
            Flows
          </button>
        </div>
      </div>

      {/* Entity Selector */}
      <div className="p-4 border-b border-[var(--color-navy-700)]">
        <label className="block text-xs font-medium text-[var(--color-text-secondary)] mb-2">
          Select {getEntityLabel()}
        </label>
        <select
          value={selectedEntityId || ''}
          onChange={(e) => dispatch(selectEntity(e.target.value))}
          disabled={isStreaming}
          className="w-full px-3 py-2 bg-[var(--color-navy-800)] border border-[var(--color-navy-700)] rounded-lg text-[var(--color-text-primary)] text-sm focus:outline-none focus:border-[var(--color-royal-500)] transition-colors disabled:opacity-50"
        >
          <option value="" disabled>
            Choose {getEntityPlaceholder()}...
          </option>
          {entities.map((entity) => (
            <option key={entity.id} value={entity.id}>
              {entity.name}
            </option>
          ))}
        </select>

        {/* Flow Mode Toggle - only show for flows */}
        {selectedEntityType === 'flow' && (
          <div className="mt-3">
            <label className="block text-xs font-medium text-[var(--color-text-secondary)] mb-2">
              Execution Mode
            </label>
            <div className="flex bg-[var(--color-navy-800)] rounded-lg p-1">
              <button
                onClick={() => handleFlowModeChange('stream')}
                disabled={isStreaming}
                className={`flex-1 flex items-center justify-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-md transition-all ${
                  flowMode === 'stream'
                    ? 'bg-[var(--color-royal-600)] text-white'
                    : 'text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)]'
                } disabled:opacity-50`}
              >
                <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
                Stream
              </button>
              <button
                onClick={() => handleFlowModeChange('async')}
                disabled={isStreaming}
                className={`flex-1 flex items-center justify-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-md transition-all ${
                  flowMode === 'async'
                    ? 'bg-[var(--color-royal-600)] text-white'
                    : 'text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)]'
                } disabled:opacity-50`}
              >
                <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
                Async
              </button>
            </div>
          </div>
        )}
      </div>

      {/* New Chat/Run Button */}
      <div className="p-4">
        <button
          onClick={handleNewChat}
          disabled={!selectedEntityId || isStreaming}
          className="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-gradient-to-r from-[var(--color-royal-600)] to-[var(--color-royal-500)] hover:from-[var(--color-royal-500)] hover:to-[var(--color-royal-400)] text-white rounded-lg font-medium text-sm transition-all disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <svg
            className="w-4 h-4"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 4v16m8-8H4"
            />
          </svg>
          {selectedEntityType === 'flow' ? 'New Run' : 'New Chat'}
        </button>
      </div>

      {/* Conversations List */}
      <div className="flex-1 overflow-y-auto">
        <div className="px-4 py-2">
          <h3 className="text-xs font-medium text-[var(--color-text-muted)] uppercase tracking-wider">
            {selectedEntityType === 'flow' ? 'Runs' : 'Conversations'}
          </h3>
        </div>
        <nav className="px-2">
          {filteredConversations.length === 0 ? (
            <p className="px-3 py-4 text-sm text-[var(--color-text-muted)] text-center">
              {selectedEntityType === 'flow' 
                ? 'No runs yet.\nStart a new run!'
                : 'No conversations yet.\nStart a new chat!'}
            </p>
          ) : (
            <ul className="space-y-1">
              {filteredConversations.map((conversation) => (
                <li key={conversation.id}>
                  <button
                    onClick={() => handleSelectConversation(conversation.id)}
                    className={`w-full group flex items-center gap-3 px-3 py-2.5 rounded-lg text-left transition-colors ${
                      activeConversationId === conversation.id
                        ? 'bg-[var(--color-royal-600)]/20 text-[var(--color-sky-300)]'
                        : 'text-[var(--color-text-secondary)] hover:bg-[var(--color-navy-800)] hover:text-[var(--color-text-primary)]'
                    }`}
                  >
                    <svg
                      className="w-4 h-4 shrink-0"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      {selectedEntityType === 'flow' ? (
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M13 10V3L4 14h7v7l9-11h-7z"
                        />
                      ) : (
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
                        />
                      )}
                    </svg>
                    <span className="flex-1 truncate text-sm">
                      {conversation.title}
                    </span>
                    <button
                      onClick={(e) => handleDeleteConversation(e, conversation.id)}
                      className="opacity-0 group-hover:opacity-100 p-1 text-[var(--color-text-muted)] hover:text-red-400 transition-all"
                      title="Delete"
                    >
                      <svg
                        className="w-4 h-4"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                        />
                      </svg>
                    </button>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </nav>
      </div>

      {/* Entity Info */}
      {selectedEntityId && (
        <div className="p-4 border-t border-[var(--color-navy-700)]">
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-green-400 animate-pulse" />
            <span className="text-xs text-[var(--color-text-muted)]">
              {getEntityLabel()} Online
            </span>
            {selectedEntityType === 'flow' && (
              <span className="ml-auto text-xs text-[var(--color-text-muted)] bg-[var(--color-navy-800)] px-2 py-0.5 rounded">
                {flowMode}
              </span>
            )}
          </div>
        </div>
      )}
    </aside>
  );
}
