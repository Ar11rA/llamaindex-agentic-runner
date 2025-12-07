import { useState } from 'react';
import type { HITLState } from '../../types';

interface HITLPromptProps {
  hitlState: HITLState;
  onRespond: (response: string) => void;
  onCancel: () => void;
  isLoading: boolean;
}

export function HITLPrompt({ hitlState, onRespond, onCancel, isLoading }: HITLPromptProps) {
  const [customResponse, setCustomResponse] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (customResponse.trim()) {
      onRespond(customResponse.trim());
      setCustomResponse('');
    }
  };

  const handleQuickResponse = (value: string) => {
    onRespond(value);
  };

  return (
    <div className="message-appear bg-gradient-to-r from-[var(--color-royal-600)]/20 to-[var(--color-sky-300)]/10 border border-[var(--color-royal-500)]/50 rounded-xl p-4 mx-4 mb-4">
      <div className="flex items-start gap-3">
        {/* Icon */}
        <div className="w-10 h-10 rounded-full bg-gradient-to-br from-[var(--color-royal-500)] to-[var(--color-sky-400)] flex items-center justify-center shrink-0">
          <svg
            className="w-5 h-5 text-white"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
        </div>

        <div className="flex-1">
          {/* Header */}
          <div className="flex items-center gap-2 mb-2">
            <h4 className="text-sm font-semibold text-[var(--color-sky-300)]">
              Input Required
            </h4>
            {hitlState.activeAgent && (
              <span className="px-2 py-0.5 text-xs bg-[var(--color-navy-800)] text-[var(--color-text-secondary)] rounded">
                from {hitlState.activeAgent}
              </span>
            )}
          </div>

          {/* Prompt message */}
          <p className="text-sm text-[var(--color-text-primary)] mb-4 leading-relaxed">
            {hitlState.prompt}
          </p>

          {/* Yes/No Buttons - Always visible */}
          <div className="flex gap-3 mb-4">
            <button
              onClick={() => handleQuickResponse('yes')}
              disabled={isLoading}
              className="flex-1 flex items-center justify-center gap-2 px-4 py-3 bg-green-600 hover:bg-green-500 text-white text-sm font-semibold rounded-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-lg shadow-green-600/20"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
              Yes
            </button>
            <button
              onClick={() => handleQuickResponse('no')}
              disabled={isLoading}
              className="flex-1 flex items-center justify-center gap-2 px-4 py-3 bg-red-600 hover:bg-red-500 text-white text-sm font-semibold rounded-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-lg shadow-red-600/20"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
              No
            </button>
          </div>

          {/* Divider */}
          <div className="flex items-center gap-3 mb-4">
            <div className="flex-1 h-px bg-[var(--color-navy-700)]" />
            <span className="text-xs text-[var(--color-text-muted)]">or type a custom response</span>
            <div className="flex-1 h-px bg-[var(--color-navy-700)]" />
          </div>

          {/* Custom response input */}
          <form onSubmit={handleSubmit} className="flex gap-2">
            <input
              type="text"
              value={customResponse}
              onChange={(e) => setCustomResponse(e.target.value)}
              placeholder="Type your response..."
              disabled={isLoading}
              className="flex-1 px-3 py-2 bg-[var(--color-navy-800)] border border-[var(--color-navy-700)] rounded-lg text-sm text-[var(--color-text-primary)] placeholder-[var(--color-text-muted)] focus:outline-none focus:border-[var(--color-royal-500)] disabled:opacity-50"
            />
            <button
              type="submit"
              disabled={!customResponse.trim() || isLoading}
              className="px-4 py-2 bg-[var(--color-royal-500)] hover:bg-[var(--color-royal-400)] text-white text-sm font-medium rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? (
                <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                </svg>
              ) : (
                'Send'
              )}
            </button>
            <button
              type="button"
              onClick={onCancel}
              disabled={isLoading}
              className="px-4 py-2 bg-[var(--color-navy-700)] hover:bg-[var(--color-navy-600)] text-[var(--color-text-secondary)] text-sm font-medium rounded-lg transition-colors disabled:opacity-50"
            >
              Cancel
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
