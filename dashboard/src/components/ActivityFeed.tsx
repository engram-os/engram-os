import { useQuery, useMutation } from '@tanstack/react-query';
import { RefreshCw, CalendarDays, Mail } from 'lucide-react';
import { apiFetch } from '../lib/api';
import { useStore } from '../lib/store';
import { cn } from '../lib/cn';

interface LogEntry {
  timestamp: string;
  actor: string;
  action: string;
  details: string;
}

interface LogsResponse {
  logs: LogEntry[];
}

const ACTION_BADGE: Record<string, string> = {
  WRITE:        'bg-emerald-50 text-emerald-700 dark:bg-emerald-900/20 dark:text-emerald-400',
  READ:         'bg-blue-50 text-blue-700 dark:bg-blue-900/20 dark:text-blue-400',
  TOOL_USE:     'bg-emerald-50 text-emerald-700 dark:bg-emerald-900/20 dark:text-emerald-400',
  DELETE:       'bg-red-50 text-red-700 dark:bg-red-900/20 dark:text-red-400',
  DELETE_BATCH: 'bg-red-50 text-red-700 dark:bg-red-900/20 dark:text-red-400',
  ERROR:        'bg-red-50 text-red-700 dark:bg-red-900/20 dark:text-red-400',
  WAKE_UP:      'bg-purple-50 text-purple-700 dark:bg-purple-900/20 dark:text-purple-400',
  SKIP:         'bg-amber-50 text-amber-700 dark:bg-amber-900/20 dark:text-amber-400',
  WARNING:      'bg-amber-50 text-amber-700 dark:bg-amber-900/20 dark:text-amber-400',
};

const ACTION_DOT: Record<string, string> = {
  WRITE:        'bg-emerald-400',
  READ:         'bg-blue-400',
  TOOL_USE:     'bg-emerald-400',
  DELETE:       'bg-red-400',
  DELETE_BATCH: 'bg-red-400',
  ERROR:        'bg-red-400',
  WAKE_UP:      'bg-purple-400',
  SKIP:         'bg-amber-300',
  WARNING:      'bg-amber-300',
};

function simplifyActor(actor: string): string {
  if (actor.startsWith('user:')) return 'User';
  if (actor.includes('calendar')) return 'Calendar';
  if (actor.includes('email')) return 'Email';
  if (actor.includes('agent')) return 'Agent';
  return actor
    .split(/[-_]/)
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(' ');
}

function dateLabel(ts: string): string {
  try {
    const date = new Date(ts.replace(' ', 'T'));
    const today = new Date();
    const yesterday = new Date(today);
    yesterday.setDate(today.getDate() - 1);
    if (date.toDateString() === today.toDateString()) return 'Today';
    if (date.toDateString() === yesterday.toDateString()) return 'Yesterday';
    return date.toLocaleDateString([], { month: 'long', day: 'numeric' });
  } catch {
    return 'Unknown date';
  }
}

function formatTime(ts: string): string {
  try {
    return new Date(ts.replace(' ', 'T')).toLocaleTimeString([], {
      hour: '2-digit',
      minute: '2-digit',
    });
  } catch {
    return ts;
  }
}

function groupByDate(logs: LogEntry[]): { label: string; entries: LogEntry[] }[] {
  const map = new Map<string, LogEntry[]>();
  for (const log of logs) {
    const label = dateLabel(log.timestamp);
    if (!map.has(label)) map.set(label, []);
    map.get(label)!.push(log);
  }
  return Array.from(map.entries()).map(([label, entries]) => ({ label, entries }));
}

function TimelineGroup({ label, entries }: { label: string; entries: LogEntry[] }) {
  return (
    <div className="mb-8">
      <p className="text-[10px] font-semibold uppercase tracking-[0.1em] text-[#8E8E93] mb-4">
        {label}
      </p>
      <div className="relative">
        {/* Vertical line */}
        <div className="absolute left-[7px] top-2 bottom-2 w-px bg-[#E5E5EA] dark:bg-[#38383A]" />

        <div className="space-y-4">
          {entries.map((log, i) => (
            <div key={i} className="relative flex gap-4 pl-7">
              {/* Dot */}
              <div className="absolute left-0 top-[5px] w-[15px] h-[15px] rounded-full bg-white dark:bg-[#121212] border border-[#E5E5EA] dark:border-[#38383A] flex items-center justify-center flex-shrink-0">
                <div className={cn(
                  'w-[7px] h-[7px] rounded-full',
                  ACTION_DOT[log.action] ?? 'bg-[#C7C7CC]'
                )} />
              </div>

              {/* Content */}
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 flex-wrap mb-1">
                  <span className={cn(
                    'px-1.5 py-0.5 rounded text-[9px] font-bold tracking-wider uppercase',
                    ACTION_BADGE[log.action] ?? 'bg-[#F2F2F7] text-[#8E8E93] dark:bg-[#2C2C2E] dark:text-[#8E8E93]'
                  )}>
                    {log.action}
                  </span>
                  <span className="text-[10px] text-[#8E8E93] tabular-nums">
                    {formatTime(log.timestamp)}
                  </span>
                  <span className="text-[10px] text-[#C7C7CC] dark:text-[#545458]">·</span>
                  <span className="text-[10px] text-[#8E8E93]">{simplifyActor(log.actor)}</span>
                </div>
                <p className="text-xs text-[#1C1C1E] dark:text-[#ECECEC] leading-relaxed break-words">
                  {log.details}
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export function ActivityFeed() {
  const { apiKey } = useStore();

  const { data, isLoading, refetch, isFetching } = useQuery<LogsResponse>({
    queryKey: ['audit-logs'],
    queryFn: async () => {
      const res = await apiFetch<LogsResponse>('/api/audit/logs?limit=60', {}, apiKey ?? '');
      return res.data ?? { logs: [] };
    },
    refetchInterval: 10_000,
    staleTime: 5_000,
  });

  const triggerCalendar = useMutation({
    mutationFn: () => apiFetch('/run-agents/calendar', { method: 'POST' }, apiKey ?? ''),
    onSuccess: () => { setTimeout(() => refetch(), 2000); },
  });

  const triggerEmail = useMutation({
    mutationFn: () => apiFetch('/run-agents/email', { method: 'POST' }, apiKey ?? ''),
    onSuccess: () => { setTimeout(() => refetch(), 2000); },
  });

  const groups = groupByDate(data?.logs ?? []);

  return (
    <div className="flex flex-col h-full bg-white dark:bg-[#121212]">
      {/* Header */}
      <div className="flex-shrink-0 flex items-center justify-between px-6 py-4 border-b border-[#E5E5EA] dark:border-[#38383A]">
        <h2 className="text-sm font-semibold text-[#1C1C1E] dark:text-[#ECECEC]">Agents</h2>
        <button
          onClick={() => refetch()}
          title="Refresh"
          className={cn(
            'p-1.5 rounded-lg text-[#8E8E93] hover:text-[#1C1C1E] dark:hover:text-[#ECECEC]',
            'hover:bg-[#F2F2F7] dark:hover:bg-[#2C2C2E] transition-colors',
            isFetching && 'animate-spin'
          )}
        >
          <RefreshCw className="w-4 h-4" />
        </button>
      </div>

      <div className="flex-1 overflow-y-auto">
        <div className="max-w-[680px] mx-auto px-6 py-8">

          {/* Trigger cards */}
          <p className="text-[10px] font-semibold uppercase tracking-[0.1em] text-[#8E8E93] mb-3">
            Trigger
          </p>
          <div className="grid grid-cols-2 gap-3 mb-10">
            <button
              onClick={() => triggerCalendar.mutate()}
              disabled={triggerCalendar.isPending}
              className={cn(
                'group flex items-center gap-3 p-4 rounded-2xl border text-left transition-all active:scale-[0.98]',
                'border-[#E5E5EA] dark:border-[#38383A]',
                'hover:border-accent-300 dark:hover:border-accent-700 hover:shadow-sm hover:-translate-y-px',
                triggerCalendar.isPending && 'opacity-40 cursor-not-allowed'
              )}
            >
              <div className="w-9 h-9 rounded-xl bg-[#F2F2F7] dark:bg-[#2C2C2E] group-hover:bg-accent-50 dark:group-hover:bg-accent-500/10 flex items-center justify-center flex-shrink-0 transition-colors">
                <CalendarDays className="w-5 h-5 text-[#1C1C1E] dark:text-[#ECECEC] group-hover:text-accent-600 dark:group-hover:text-accent-400 transition-colors" />
              </div>
              <div>
                <p className="text-sm font-medium text-[#1C1C1E] dark:text-[#ECECEC]">Calendar</p>
                <p className="text-xs text-[#8E8E93] mt-0.5">
                  {triggerCalendar.isPending ? 'Running…' : triggerCalendar.isSuccess ? 'Triggered ✓' : 'Schedule events from memory'}
                </p>
              </div>
            </button>

            <button
              onClick={() => triggerEmail.mutate()}
              disabled={triggerEmail.isPending}
              className={cn(
                'group flex items-center gap-3 p-4 rounded-2xl border text-left transition-all active:scale-[0.98]',
                'border-[#E5E5EA] dark:border-[#38383A]',
                'hover:border-accent-300 dark:hover:border-accent-700 hover:shadow-sm hover:-translate-y-px',
                triggerEmail.isPending && 'opacity-40 cursor-not-allowed'
              )}
            >
              <div className="w-9 h-9 rounded-xl bg-[#F2F2F7] dark:bg-[#2C2C2E] group-hover:bg-accent-50 dark:group-hover:bg-accent-500/10 flex items-center justify-center flex-shrink-0 transition-colors">
                <Mail className="w-5 h-5 text-[#1C1C1E] dark:text-[#ECECEC] group-hover:text-accent-600 dark:group-hover:text-accent-400 transition-colors" />
              </div>
              <div>
                <p className="text-sm font-medium text-[#1C1C1E] dark:text-[#ECECEC]">Email</p>
                <p className="text-xs text-[#8E8E93] mt-0.5">
                  {triggerEmail.isPending ? 'Running…' : triggerEmail.isSuccess ? 'Triggered ✓' : 'Process and draft replies'}
                </p>
              </div>
            </button>
          </div>

          {/* Timeline */}
          <p className="text-[10px] font-semibold uppercase tracking-[0.1em] text-[#8E8E93] mb-4">
            Activity
          </p>

          {isLoading ? (
            <div className="text-sm text-[#8E8E93] text-center py-12">Loading…</div>
          ) : groups.length === 0 ? (
            <div className="text-sm text-[#8E8E93] text-center py-12 leading-relaxed">
              No activity yet.
              <br />
              Trigger an agent above to see entries here.
            </div>
          ) : (
            groups.map(({ label, entries }) => (
              <TimelineGroup key={label} label={label} entries={entries} />
            ))
          )}
        </div>
      </div>
    </div>
  );
}
