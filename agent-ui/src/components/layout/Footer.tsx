export function Footer() {
  return (
    <footer className="h-10 bg-[var(--color-navy-900)] border-t border-[var(--color-navy-700)] flex items-center justify-center px-6 shrink-0">
      <p className="text-xs text-[var(--color-text-muted)]">
        Powered by{' '}
        <span className="text-[var(--color-royal-400)]">LlamaIndex Agents</span>
        {' · '}
        <span className="text-[var(--color-text-secondary)]">
          © {new Date().getFullYear()}
        </span>
      </p>
    </footer>
  );
}

