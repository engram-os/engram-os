import { useState } from 'react';
import { apiFetch } from '../lib/api';
import { useStore } from '../lib/store';
import { cn } from '../lib/cn';

interface MeResponse {
  user_id: string;
  role: string;
}

export function AuthScreen() {
  const [key, setKey] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { setAuth, darkMode } = useStore();

  async function connect(submittedKey: string) {
    setLoading(true);
    setError('');

    const result = await apiFetch<MeResponse>('/api/me', {}, submittedKey);
    setLoading(false);

    if (result.status === 200 && result.data) {
      setAuth(submittedKey, result.data.role);
    } else if (result.status === 401 || result.status === 403) {
      setError('Invalid API key.');
    } else if (result.status === 0) {
      setError('Cannot reach Engram. Is the brain running?');
    } else {
      setError(`Connection failed (HTTP ${result.status}).`);
    }
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    connect(key.trim());
  }

  return (
    <div
      className={cn(
        'min-h-screen flex items-center justify-center font-sans',
        darkMode ? 'bg-[#212121] text-[#ECECEC]' : 'bg-[#FAFAF9] text-[#0D0D0D]'
      )}
    >
      <div className="w-full max-w-[360px] px-6">
        <div className="mb-8">
          <p className="text-[10px] font-mono uppercase tracking-[0.15em] text-neutral-500 mb-3">
            Engram OS
          </p>
          <h1 className="text-2xl font-semibold tracking-tight leading-tight">
            Command Center
          </h1>
          <p className="text-sm text-neutral-500 mt-1.5 leading-relaxed">
            Enter your API key to connect.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-2.5">
          <input
            type="password"
            value={key}
            onChange={(e) => setKey(e.target.value)}
            placeholder="ENGRAM_API_KEY"
            autoFocus
            className={cn(
              'w-full px-3.5 py-2.5 rounded-lg border text-sm font-mono outline-none transition-colors',
              darkMode
                ? 'bg-[#2A2A2A] border-[#383838] text-[#ECECEC] placeholder:text-neutral-600 focus:border-neutral-500'
                : 'bg-white border-[#E8E8E8] text-[#0D0D0D] placeholder:text-neutral-400 focus:border-neutral-400'
            )}
          />

          {error && <p className="text-xs text-red-500 font-medium">{error}</p>}

          <button
            type="submit"
            disabled={loading}
            className={cn(
              'w-full py-2.5 rounded-lg text-sm font-medium transition-opacity',
              darkMode ? 'bg-[#ECECEC] text-[#0D0D0D]' : 'bg-[#0D0D0D] text-white',
              loading && 'opacity-50 cursor-not-allowed'
            )}
          >
            {loading ? 'Connecting...' : 'Connect'}
          </button>
        </form>

        <button
          onClick={() => connect('')}
          className="mt-5 text-xs text-neutral-500 hover:text-neutral-400 transition-colors w-full text-center"
        >
          Dev mode — skip (no API key configured)
        </button>
      </div>
    </div>
  );
}
