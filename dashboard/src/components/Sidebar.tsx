import { useQuery, useQueryClient } from '@tanstack/react-query';
import { SquarePen, Bot, Settings, Folder, FolderOpen, Plus, Library } from 'lucide-react';
import { apiFetch } from '../lib/api';
import { useStore, type View } from '../lib/store';
import { cn } from '../lib/cn';

interface Matter { id: string; name: string; }
interface MattersResponse { matters: Matter[]; }

function NavItem({
  icon,
  label,
  active,
  onClick,
}: {
  icon: React.ReactNode;
  label: string;
  active?: boolean;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className={cn(
        'w-full flex items-center gap-2.5 px-2.5 py-1.5 rounded-lg text-sm transition-colors text-left active:scale-[0.98]',
        active
          ? 'bg-accent-500/10 text-[#1C1C1E] dark:text-white font-medium'
          : 'text-[#1C1C1E] dark:text-[#ECECEC] hover:bg-black/[0.04] dark:hover:bg-white/[0.05]'
      )}
    >
      <span className={cn('flex-shrink-0', active ? 'text-accent-600 dark:text-accent-400' : 'text-[#8E8E93]')}>
        {icon}
      </span>
      <span className="truncate">{label}</span>
    </button>
  );
}

export function Sidebar() {
  const {
    apiKey, userRole, view, setView,
    activeMatterId, setActiveMatter,
    clearMessages,
  } = useStore();
  const qc = useQueryClient();

  const { data: mattersData } = useQuery<MattersResponse>({
    queryKey: ['matters'],
    queryFn: async () => {
      const r = await apiFetch<MattersResponse>('/api/matters', {}, apiKey ?? '');
      return r.data ?? { matters: [] };
    },
    staleTime: 30_000,
  });
  const matters = mattersData?.matters ?? [];

  function navTo(v: View) {
    setView(v);
    qc.invalidateQueries({ queryKey: ['matters'] });
  }

  return (
    <aside className="w-[220px] flex-shrink-0 flex flex-col bg-[#F2F2F7] dark:bg-[#1C1C1E] border-r border-[#E5E5EA] dark:border-[#38383A] overflow-y-auto">
      {/* Wordmark */}
      <div className="px-4 pt-5 pb-3 flex items-center gap-2">
        <div className="w-5 h-5 rounded-md bg-gradient-to-br from-accent-400 to-accent-600 flex items-center justify-center shadow-sm">
          <span className="text-[10px] font-bold text-white leading-none">E</span>
        </div>
        <span className="text-sm font-semibold tracking-tight text-[#1C1C1E] dark:text-[#F5F5F5]">
          Engram
        </span>
      </div>

      {/* Top nav */}
      <nav className="px-2 space-y-0.5">
        <NavItem
          icon={<SquarePen className="w-4 h-4" />}
          label="New chat"
          onClick={() => { clearMessages(); navTo('chat'); }}
        />
        <NavItem
          icon={<Bot className="w-4 h-4" />}
          label="Agents"
          active={view === 'agents'}
          onClick={() => navTo('agents')}
        />
        <NavItem
          icon={<Library className="w-4 h-4" />}
          label="Memories"
          active={view === 'memories'}
          onClick={() => navTo('memories')}
        />
        <NavItem
          icon={<Settings className="w-4 h-4" />}
          label="Settings"
          active={view === 'settings'}
          onClick={() => navTo('settings')}
        />
      </nav>

      {/* Matters section */}
      <div className="mt-4 px-2">
        <p className="px-2.5 mb-1 text-[10px] font-semibold uppercase tracking-[0.1em] text-[#8E8E93]">
          Projects
        </p>

        {/* All memories */}
        <button
          onClick={() => { setActiveMatter(null, 'All memories'); navTo('chat'); }}
          className={cn(
            'w-full flex items-center gap-2.5 px-2.5 py-1.5 rounded-lg text-sm transition-colors active:scale-[0.98]',
            activeMatterId === null && view === 'chat'
              ? 'bg-accent-500/10 font-medium text-[#1C1C1E] dark:text-white'
              : 'text-[#1C1C1E] dark:text-[#ECECEC] hover:bg-black/[0.04] dark:hover:bg-white/[0.05]'
          )}
        >
          <FolderOpen className={cn(
            'w-4 h-4 flex-shrink-0',
            activeMatterId === null && view === 'chat' ? 'text-accent-600 dark:text-accent-400' : 'text-[#8E8E93]'
          )} />
          <span className="truncate">All memories</span>
        </button>

        {matters.map((m) => (
          <button
            key={m.id}
            onClick={() => { setActiveMatter(m.id, m.name); navTo('chat'); }}
            className={cn(
              'w-full flex items-center gap-2.5 px-2.5 py-1.5 rounded-lg text-sm transition-colors active:scale-[0.98]',
              activeMatterId === m.id && view === 'chat'
                ? 'bg-accent-500/10 font-medium text-[#1C1C1E] dark:text-white'
                : 'text-[#1C1C1E] dark:text-[#ECECEC] hover:bg-black/[0.04] dark:hover:bg-white/[0.05]'
            )}
          >
            <Folder className={cn(
              'w-4 h-4 flex-shrink-0',
              activeMatterId === m.id && view === 'chat' ? 'text-accent-600 dark:text-accent-400' : 'text-[#8E8E93]'
            )} />
            <span className="truncate">{m.name}</span>
          </button>
        ))}

        <button
          onClick={() => navTo('settings')}
          className="w-full flex items-center gap-2.5 px-2.5 py-1.5 rounded-lg text-sm text-[#8E8E93] hover:text-[#1C1C1E] dark:hover:text-[#ECECEC] hover:bg-black/[0.04] dark:hover:bg-white/[0.05] transition-colors mt-0.5"
        >
          <Plus className="w-4 h-4 flex-shrink-0" />
          <span>New project</span>
        </button>
      </div>

      <div className="flex-1" />

      {/* Footer */}
      <div className="px-4 py-3 border-t border-[#E5E5EA] dark:border-[#38383A]">
        <p className="text-[9px] text-[#8E8E93]">
          Engram v1.7.0{userRole === 'admin' && ' · admin'}
        </p>
      </div>
    </aside>
  );
}
