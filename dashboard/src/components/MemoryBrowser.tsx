import { useState, useCallback } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { Trash2, ChevronDown } from 'lucide-react';
import { apiFetch } from '../lib/api';
import { useStore } from '../lib/store';
import { cn } from '../lib/cn';

interface Memory {
  id: string;
  memory: string;
  type: string;
  matter_id: string;
  classification: string;
  created_at: string;
}

interface MemoriesResponse {
  memories: Memory[];
  next_offset: string | null;
}

interface MattersResponse {
  matters: Array<{ id: string; name: string }>;
}

const CONTENT_TYPES = ['', 'explicit_memory', 'raw_ingestion', 'file_ingest', 'browsing_event'];
const CLASSIFICATIONS = ['', 'PUBLIC', 'INTERNAL', 'CONFIDENTIAL', 'PHI', 'PII', 'RESTRICTED'];

const CLF_COLORS: Record<string, string> = {
  PHI: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
  PII: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
  RESTRICTED: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
  CONFIDENTIAL: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400',
  INTERNAL: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
  PUBLIC: 'bg-[#F2F2F7] text-[#8E8E93] dark:bg-[#2C2C2E] dark:text-[#8E8E93]',
};

function ClassificationBadge({ clf }: { clf: string }) {
  return (
    <span className={cn(
      'inline-flex items-center px-1.5 py-0.5 rounded text-[9px] font-bold tracking-widest uppercase',
      CLF_COLORS[clf] ?? CLF_COLORS.PUBLIC,
    )}>
      {clf || 'PUBLIC'}
    </span>
  );
}

function TypeChip({ type }: { type: string }) {
  const label = type.replace(/_/g, ' ');
  return (
    <span className="text-[10px] text-[#8E8E93] bg-[#F2F2F7] dark:bg-[#2C2C2E] px-1.5 py-0.5 rounded">
      {label}
    </span>
  );
}

function FilterSelect({
  label, value, options, onChange,
}: {
  label: string;
  value: string;
  options: string[];
  onChange: (v: string) => void;
}) {
  return (
    <div className="relative flex items-center">
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="appearance-none text-xs bg-white dark:bg-[#1C1C1E] border border-[#E5E5EA] dark:border-[#38383A] rounded-lg pl-2.5 pr-7 py-1.5 text-[#1C1C1E] dark:text-[#ECECEC] outline-none cursor-pointer"
      >
        <option value="">{label}</option>
        {options.filter(Boolean).map((o) => (
          <option key={o} value={o}>{o.replace(/_/g, ' ')}</option>
        ))}
      </select>
      <ChevronDown className="absolute right-2 w-3 h-3 text-[#8E8E93] pointer-events-none" />
    </div>
  );
}

export function MemoryBrowser() {
  const { apiKey } = useStore();
  const qc = useQueryClient();

  const [filterType, setFilterType] = useState('');
  const [filterMatter, setFilterMatter] = useState('');
  const [filterClf, setFilterClf] = useState('');
  const [pages, setPages] = useState<Memory[]>([]);
  const [nextOffset, setNextOffset] = useState<string | null>(null);
  const [hasLoaded, setHasLoaded] = useState(false);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const { data: mattersData } = useQuery<MattersResponse>({
    queryKey: ['matters'],
    queryFn: async () => {
      const r = await apiFetch<MattersResponse>('/api/matters', {}, apiKey ?? '');
      return r.data ?? { matters: [] };
    },
    staleTime: 60_000,
  });
  const matters = mattersData?.matters ?? [];

  const buildUrl = useCallback((offset?: string) => {
    const params = new URLSearchParams();
    if (filterType) params.set('type', filterType);
    if (filterMatter) params.set('matter_id', filterMatter);
    if (filterClf) params.set('classification', filterClf);
    params.set('limit', '20');
    if (offset) params.set('offset', offset);
    return `/api/memories?${params}`;
  }, [filterType, filterMatter, filterClf]);

  async function load(reset = false) {
    const offset = reset ? undefined : nextOffset ?? undefined;
    const r = await apiFetch<MemoriesResponse>(buildUrl(offset), {}, apiKey ?? '');
    if (!r.data) return;
    setPages((prev) => reset ? r.data!.memories : [...prev, ...r.data!.memories]);
    setNextOffset(r.data.next_offset);
    setHasLoaded(true);
  }

  function applyFilters() {
    setPages([]);
    setNextOffset(null);
    setHasLoaded(false);
    load(true);
  }

  async function deleteMemory(id: string) {
    setDeletingId(id);
    await apiFetch(`/api/memory/${id}`, { method: 'DELETE' }, apiKey ?? '');
    setPages((prev) => prev.filter((m) => m.id !== id));
    qc.invalidateQueries({ queryKey: ['matters'] });
    setDeletingId(null);
  }

  return (
    <div className="flex flex-col h-full bg-white dark:bg-[#121212]">
      {/* Header */}
      <div className="flex-shrink-0 flex items-center justify-between px-6 py-4 border-b border-[#E5E5EA] dark:border-[#38383A]">
        <h2 className="text-sm font-semibold text-[#1C1C1E] dark:text-[#ECECEC]">Memories</h2>
        <span className="text-xs text-[#8E8E93]">{pages.length} loaded</span>
      </div>

      {/* Filters */}
      <div className="flex-shrink-0 flex items-center gap-2 px-6 py-3 border-b border-[#E5E5EA] dark:border-[#38383A]">
        <FilterSelect
          label="All types"
          value={filterType}
          options={CONTENT_TYPES}
          onChange={setFilterType}
        />
        {/* Matter filter needs separate label/value — not using FilterSelect */}
        <div className="relative flex items-center">
          <select
            value={filterMatter}
            onChange={(e) => setFilterMatter(e.target.value)}
            className="appearance-none text-xs bg-white dark:bg-[#1C1C1E] border border-[#E5E5EA] dark:border-[#38383A] rounded-lg pl-2.5 pr-7 py-1.5 text-[#1C1C1E] dark:text-[#ECECEC] outline-none cursor-pointer"
          >
            <option value="">All projects</option>
            {matters.map((m) => (
              <option key={m.id} value={m.id}>{m.name}</option>
            ))}
          </select>
          <ChevronDown className="absolute right-2 w-3 h-3 text-[#8E8E93] pointer-events-none" />
        </div>
        <FilterSelect
          label="All classifications"
          value={filterClf}
          options={CLASSIFICATIONS}
          onChange={setFilterClf}
        />
        <button
          onClick={applyFilters}
          className="ml-auto text-xs px-3 py-1.5 rounded-lg bg-[#1C1C1E] dark:bg-[#ECECEC] text-white dark:text-[#1C1C1E] font-medium hover:opacity-80 transition-opacity"
        >
          Search
        </button>
      </div>

      {/* List */}
      <div className="flex-1 overflow-y-auto px-6 py-4">
        {!hasLoaded ? (
          <div className="flex flex-col items-center justify-center h-full gap-3">
            <p className="text-sm text-[#8E8E93]">Apply filters and press Search, or</p>
            <button
              onClick={() => load(true)}
              className="text-sm text-[#1C1C1E] dark:text-[#ECECEC] underline underline-offset-2"
            >
              load all memories
            </button>
          </div>
        ) : pages.length === 0 ? (
          <p className="text-sm text-[#8E8E93] text-center mt-16">No memories match these filters.</p>
        ) : (
          <div className="space-y-2 max-w-3xl mx-auto">
            {pages.map((mem) => (
              <div
                key={mem.id}
                className="group flex items-start gap-3 px-4 py-3 rounded-xl border border-[#E5E5EA] dark:border-[#38383A] bg-white dark:bg-[#1C1C1E] hover:border-[#C7C7CC] dark:hover:border-[#545458] transition-colors"
              >
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-[#1C1C1E] dark:text-[#ECECEC] leading-relaxed line-clamp-3">
                    {mem.memory}
                  </p>
                  <div className="flex items-center gap-2 mt-2 flex-wrap">
                    <ClassificationBadge clf={mem.classification} />
                    <TypeChip type={mem.type} />
                    {mem.created_at && (
                      <span className="text-[10px] text-[#8E8E93]">
                        {new Date(mem.created_at).toLocaleDateString()}
                      </span>
                    )}
                  </div>
                </div>
                <button
                  onClick={() => deleteMemory(mem.id)}
                  disabled={deletingId === mem.id}
                  className="flex-shrink-0 p-1.5 rounded-lg text-[#8E8E93] opacity-0 group-hover:opacity-100 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 transition-all disabled:opacity-30"
                  title="Delete memory"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              </div>
            ))}

            {nextOffset && (
              <button
                onClick={() => load()}
                className="w-full py-2.5 text-sm text-[#8E8E93] hover:text-[#1C1C1E] dark:hover:text-[#ECECEC] transition-colors"
              >
                Load more
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
