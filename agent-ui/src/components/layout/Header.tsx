import { useAppSelector } from '../../store';

export function Header() {
  const { agents, teams, flows, selectedEntityId, selectedEntityType, currentAgentName } = useAppSelector(
    (state) => state.chat
  );

  const selectedEntity =
    selectedEntityType === 'agent'
      ? agents.find((a) => a.id === selectedEntityId)
      : selectedEntityType === 'team'
      ? teams.find((t) => t.id === selectedEntityId)
      : flows.find((f) => f.id === selectedEntityId);

  const getEntityTypeLabel = () => {
    switch (selectedEntityType) {
      case 'agent': return 'Agent';
      case 'team': return 'Team';
      case 'flow': return 'Flow';
    }
  };

  return (
    <header className="h-14 bg-[var(--color-navy-900)] border-b border-[var(--color-navy-700)] flex items-center justify-between px-6 shrink-0">
      <div className="flex items-center gap-3">
        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-[var(--color-royal-500)] to-[var(--color-sky-300)] flex items-center justify-center">
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
              d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"
            />
          </svg>
        </div>
        <h1 className="text-lg font-semibold text-[var(--color-text-primary)]">
          Agent Chat
        </h1>
      </div>

      <div className="flex items-center gap-4">
        {/* Current responding agent (for teams) */}
        {currentAgentName && (
          <div className="flex items-center gap-2">
            <div className="flex gap-1">
              <span className="w-1.5 h-1.5 bg-[var(--color-sky-300)] rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
              <span className="w-1.5 h-1.5 bg-[var(--color-sky-300)] rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
              <span className="w-1.5 h-1.5 bg-[var(--color-sky-300)] rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
            </div>
            <span className="text-sm text-[var(--color-sky-300)] font-medium">
              {currentAgentName}
            </span>
          </div>
        )}

        {selectedEntity && (
          <div className="flex items-center gap-2">
            <span className="text-sm text-[var(--color-text-secondary)]">
              Active {getEntityTypeLabel()}:
            </span>
            <span className="px-3 py-1 text-sm font-medium text-[var(--color-sky-300)] bg-[var(--color-navy-800)] rounded-full">
              {selectedEntity.name}
            </span>
          </div>
        )}
      </div>
    </header>
  );
}
