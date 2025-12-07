import type { Message } from '../../types';

interface MessageBubbleProps {
  message: Message;
}

export function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === 'user';
  const isAssistant = message.role === 'assistant';

  return (
    <div
      className={`message-appear flex ${isUser ? 'justify-end' : 'justify-start'}`}
    >
      <div
        className={`max-w-[75%] rounded-2xl px-4 py-3 ${
          isUser
            ? 'bg-gradient-to-r from-[var(--color-royal-600)] to-[var(--color-royal-500)] text-white'
            : 'bg-[var(--color-navy-800)] text-[var(--color-text-primary)] border border-[var(--color-navy-700)]'
        }`}
      >
        {/* Role indicator for assistant */}
        {isAssistant && (
          <div className="flex items-center gap-2 mb-2 pb-2 border-b border-[var(--color-navy-700)]">
            <div className="w-5 h-5 rounded-full bg-gradient-to-br from-[var(--color-sky-300)] to-[var(--color-royal-500)] flex items-center justify-center">
              <svg
                className="w-3 h-3 text-white"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
                />
              </svg>
            </div>
            <span className="text-xs font-medium text-[var(--color-sky-300)]">
              {message.agentName || 'Assistant'}
            </span>
          </div>
        )}

        {/* Message content */}
        <div className="whitespace-pre-wrap break-words text-sm leading-relaxed">
          {message.content || (message.isStreaming && (
            <span className="text-[var(--color-text-muted)]">Thinking...</span>
          ))}
          {message.isStreaming && message.content && (
            <span className="cursor-blink" />
          )}
        </div>

        {/* Timestamp */}
        <div
          className={`mt-2 text-xs ${
            isUser ? 'text-white/60' : 'text-[var(--color-text-muted)]'
          }`}
        >
          {new Date(message.timestamp).toLocaleTimeString([], {
            hour: '2-digit',
            minute: '2-digit',
          })}
        </div>
      </div>
    </div>
  );
}
