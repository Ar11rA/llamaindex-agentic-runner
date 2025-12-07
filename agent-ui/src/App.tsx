import { useEffect } from 'react';
import { useAppDispatch, useAppSelector } from './store';
import { fetchAgents, fetchTeams, fetchFlows } from './store/chatSlice';
import { Header } from './components/layout/Header';
import { Footer } from './components/layout/Footer';
import { Sidebar } from './components/layout/Sidebar';
import { ChatWindow } from './components/chat/ChatWindow';

function App() {
  const dispatch = useAppDispatch();
  const { isLoading, error } = useAppSelector((state) => state.chat);

  // Fetch agents, teams, and flows on mount
  useEffect(() => {
    dispatch(fetchAgents());
    dispatch(fetchTeams());
    dispatch(fetchFlows());
  }, [dispatch]);

  return (
    <div className="h-screen flex flex-col bg-[var(--color-navy-950)]">
      <Header />

      <div className="flex-1 flex overflow-hidden">
        <Sidebar />

        <main className="flex-1 flex flex-col overflow-hidden">
          {isLoading && !error ? (
            <div className="flex-1 flex items-center justify-center">
              <div className="flex flex-col items-center gap-4">
                <div className="w-12 h-12 border-4 border-[var(--color-navy-700)] border-t-[var(--color-royal-500)] rounded-full animate-spin" />
                <p className="text-sm text-[var(--color-text-muted)]">
                  Loading...
                </p>
              </div>
            </div>
          ) : error ? (
            <div className="flex-1 flex items-center justify-center">
              <div className="text-center max-w-md">
                <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-red-500/20 flex items-center justify-center">
                  <svg
                    className="w-8 h-8 text-red-400"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                    />
                  </svg>
                </div>
                <h3 className="text-lg font-medium text-[var(--color-text-primary)] mb-2">
                  Connection Error
                </h3>
                <p className="text-sm text-[var(--color-text-muted)] mb-4">
                  {error}
                </p>
                <button
                  onClick={() => {
                    dispatch(fetchAgents());
                    dispatch(fetchTeams());
                    dispatch(fetchFlows());
                  }}
                  className="px-4 py-2 bg-[var(--color-royal-500)] hover:bg-[var(--color-royal-400)] text-white text-sm font-medium rounded-lg transition-colors"
                >
                  Retry
                </button>
              </div>
            </div>
          ) : (
            <ChatWindow />
          )}
        </main>
      </div>

      <Footer />
    </div>
  );
}

export default App;
