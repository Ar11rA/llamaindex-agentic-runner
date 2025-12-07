import { useAppSelector } from '../../store';
import { MessageList } from './MessageList';
import { ChatInput } from './ChatInput';
import { HITLPrompt } from './HITLPrompt';
import { useChat } from '../../hooks/useChat';

export function ChatWindow() {
  const {
    conversations,
    activeConversationId,
    hitlState,
    isStreaming,
    selectedEntityId,
    selectedEntityType,
  } = useAppSelector((state) => state.chat);

  const { sendMessage, respondToHITL, cancelStream } = useChat();

  const activeConversation = conversations.find((c) => c.id === activeConversationId);

  // Get entity type specific labels
  const getEntityLabel = () => {
    switch (selectedEntityType) {
      case 'agent': return 'an agent';
      case 'team': return 'a team';
      case 'flow': return 'a flow';
    }
  };

  const getActionLabel = () => {
    return selectedEntityType === 'flow' ? 'New Run' : 'New Chat';
  };

  // No conversation selected
  if (!activeConversation) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center bg-[var(--color-navy-950)]">
        <div className="text-center">
          <div className="w-20 h-20 mx-auto mb-6 rounded-2xl bg-gradient-to-br from-[var(--color-royal-600)] to-[var(--color-sky-300)] flex items-center justify-center">
            {selectedEntityType === 'flow' ? (
              <svg
                className="w-10 h-10 text-white"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={1.5}
                  d="M13 10V3L4 14h7v7l9-11h-7z"
                />
              </svg>
            ) : (
              <svg
                className="w-10 h-10 text-white"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={1.5}
                  d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"
                />
              </svg>
            )}
          </div>
          <h2 className="text-xl font-semibold text-[var(--color-text-primary)] mb-2">
            {selectedEntityType === 'flow' ? 'Welcome to Flows' : 'Welcome to Agent Chat'}
          </h2>
          <p className="text-sm text-[var(--color-text-muted)] max-w-md">
            {selectedEntityId
              ? `Click "${getActionLabel()}" to start ${selectedEntityType === 'flow' ? 'running' : 'chatting with'} the selected ${selectedEntityType}.`
              : `Select ${getEntityLabel()} from the sidebar to get started.`}
          </p>
        </div>
      </div>
    );
  }

  const handleSend = (message: string) => {
    sendMessage(message);
  };

  const handleHITLRespond = (response: string) => {
    respondToHITL(response);
  };

  const handleCancel = () => {
    cancelStream();
  };

  // Get placeholder text based on entity type
  const getInputPlaceholder = () => {
    if (selectedEntityType === 'flow') {
      return 'Enter a topic to run the flow...';
    }
    return 'Type your message... (Shift+Enter for new line)';
  };

  return (
    <div className="flex-1 flex flex-col bg-[var(--color-navy-950)] overflow-hidden">
      {/* Messages */}
      <MessageList messages={activeConversation.messages} />

      {/* HITL Prompt */}
      {hitlState && (
        <HITLPrompt
          hitlState={hitlState}
          onRespond={handleHITLRespond}
          onCancel={handleCancel}
          isLoading={isStreaming}
        />
      )}

      {/* Input */}
      <ChatInput
        onSend={handleSend}
        onCancel={handleCancel}
        disabled={!selectedEntityId || !!hitlState}
        isStreaming={isStreaming}
        placeholder={getInputPlaceholder()}
      />
    </div>
  );
}
