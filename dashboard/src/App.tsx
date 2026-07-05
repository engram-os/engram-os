import { useEffect } from 'react';
import { QueryClientProvider } from '@tanstack/react-query';
import { queryClient } from './lib/query';
import { useStore } from './lib/store';
import { AuthScreen } from './components/AuthScreen';
import { Sidebar } from './components/Sidebar';
import { Chat } from './components/Chat';
import { ActivityFeed } from './components/ActivityFeed';
import { MemoryBrowser } from './components/MemoryBrowser';
import { SettingsPanel } from './components/SettingsPanel';

export default function App() {
  const { apiKey, darkMode, view } = useStore();

  useEffect(() => {
    document.documentElement.classList.toggle('dark', darkMode);
  }, [darkMode]);

  return (
    <QueryClientProvider client={queryClient}>
      {apiKey === null ? (
        <AuthScreen />
      ) : (
        <div className="flex h-screen bg-white dark:bg-[#121212] text-[#1C1C1E] dark:text-[#ECECEC] overflow-hidden font-sans">
          <Sidebar />
          <main className="flex-1 overflow-hidden">
            {/* key={view} remounts the wrapper on navigation so the fade replays */}
            <div key={view} className="h-full animate-fade-in">
              {view === 'chat' && <Chat />}
              {view === 'agents' && <ActivityFeed />}
              {view === 'memories' && <MemoryBrowser />}
              {view === 'settings' && <SettingsPanel />}
            </div>
          </main>
        </div>
      )}
    </QueryClientProvider>
  );
}
