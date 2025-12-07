import { useState, useRef, useEffect } from 'react';

interface ChatInputProps {
  onSend: (message: string) => void;
  onCancel: () => void;
  disabled: boolean;
  isStreaming: boolean;
  placeholder?: string;
}

export function ChatInput({ onSend, onCancel, disabled, isStreaming, placeholder }: ChatInputProps) {
  const [message, setMessage] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-resize textarea
  useEffect(() => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = 'auto';
      textarea.style.height = Math.min(textarea.scrollHeight, 200) + 'px';
    }
  }, [message]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (message.trim() && !disabled) {
      onSend(message.trim());
      setMessage('');
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <div className="border-t border-[var(--color-navy-700)] bg-[var(--color-navy-900)] p-4">
      <form onSubmit={handleSubmit} className="max-w-3xl mx-auto">
        <div className="relative flex items-end gap-3 bg-[var(--color-navy-800)] border border-[var(--color-navy-700)] rounded-xl p-2 focus-within:border-[var(--color-royal-500)] transition-colors">
          <textarea
            ref={textareaRef}
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={placeholder || "Type your message... (Shift+Enter for new line)"}
            disabled={disabled}
            rows={1}
            className="flex-1 bg-transparent text-[var(--color-text-primary)] text-sm placeholder-[var(--color-text-muted)] resize-none focus:outline-none px-2 py-1.5 max-h-[200px] disabled:opacity-50"
          />

          <div className="flex items-center gap-2 shrink-0">
            {isStreaming ? (
              <button
                type="button"
                onClick={onCancel}
                className="flex items-center justify-center w-9 h-9 bg-red-600 hover:bg-red-500 text-white rounded-lg transition-colors"
                title="Cancel generation"
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
                    d="M6 18L18 6M6 6l12 12"
                  />
                </svg>
              </button>
            ) : (
              <button
                type="submit"
                disabled={!message.trim() || disabled}
                className="flex items-center justify-center w-9 h-9 bg-[var(--color-royal-500)] hover:bg-[var(--color-royal-400)] text-white rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                title="Send message"
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
                    d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"
                  />
                </svg>
              </button>
            )}
          </div>
        </div>

        {isStreaming && (
          <div className="flex items-center justify-center gap-2 mt-2 text-xs text-[var(--color-text-muted)]">
            <div className="flex gap-1">
              <span className="w-1.5 h-1.5 bg-[var(--color-royal-400)] rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
              <span className="w-1.5 h-1.5 bg-[var(--color-royal-400)] rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
              <span className="w-1.5 h-1.5 bg-[var(--color-royal-400)] rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
            </div>
            <span>Processing...</span>
          </div>
        )}
      </form>
    </div>
  );
}
