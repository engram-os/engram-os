import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { ArrowLeft, Sun, Moon, LogOut } from 'lucide-react';
import { apiFetch } from '../lib/api';
import { useStore } from '../lib/store';
import { cn } from '../lib/cn';

interface Matter { id: string; name: string; }
interface MattersResponse { matters: Matter[]; }
interface User { user_id: string; display_name: string; role: string; }
interface UsersResponse { users: User[]; }
interface CreateUserResponse { user_id: string; api_key: string; display_name: string; }

function SectionLabel({ children }: { children: React.ReactNode }) {
  return (
    <p className="text-[10px] font-semibold uppercase tracking-[0.12em] text-[#8E8E93] mb-3">
      {children}
    </p>
  );
}

function Field({ label, children }: { label?: string; children: React.ReactNode }) {
  return (
    <div className="space-y-1.5">
      {label && <label className="text-xs text-[#8E8E93]">{label}</label>}
      {children}
    </div>
  );
}

function TextInput(props: React.InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input
      {...props}
      className={cn(
        'w-full px-3 py-2 rounded-lg border text-sm outline-none transition-colors',
        'bg-white dark:bg-[#1C1C1E]',
        'border-[#E5E5EA] dark:border-[#38383A]',
        'text-[#1C1C1E] dark:text-[#ECECEC]',
        'placeholder:text-[#8E8E93]',
        'focus:border-accent-300 dark:focus:border-accent-700',
        props.className
      )}
    />
  );
}

function SelectInput({
  value,
  onChange,
  options,
}: {
  value: string;
  onChange: (v: string) => void;
  options: { value: string; label: string }[];
}) {
  return (
    <select
      value={value}
      onChange={(e) => onChange(e.target.value)}
      className="w-full px-3 py-2 rounded-lg border text-sm outline-none transition-colors bg-white dark:bg-[#1C1C1E] border-[#E5E5EA] dark:border-[#38383A] text-[#1C1C1E] dark:text-[#ECECEC] focus:border-[#8E8E93]"
    >
      {options.map((o) => (
        <option key={o.value} value={o.value}>{o.label}</option>
      ))}
    </select>
  );
}

function Btn({
  children,
  onClick,
  variant = 'default',
  disabled,
  fullWidth,
}: {
  children: React.ReactNode;
  onClick?: () => void;
  variant?: 'default' | 'primary' | 'danger';
  disabled?: boolean;
  fullWidth?: boolean;
}) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={cn(
        'px-4 py-2 rounded-lg text-sm font-medium transition-all active:scale-[0.98]',
        fullWidth && 'w-full',
        variant === 'primary' && 'bg-accent-500 text-white hover:bg-accent-600',
        variant === 'default' && 'border border-[#E5E5EA] dark:border-[#38383A] text-[#1C1C1E] dark:text-[#ECECEC] hover:bg-[#F2F2F7] dark:hover:bg-[#2C2C2E]',
        variant === 'danger' && 'border border-red-200 dark:border-red-900 text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20',
        disabled && 'opacity-40 cursor-not-allowed pointer-events-none'
      )}
    >
      {children}
    </button>
  );
}

function StatusMsg({ ok, text }: { ok: boolean; text: string }) {
  return (
    <p className={cn('text-xs', ok ? 'text-emerald-600 dark:text-emerald-400' : 'text-red-600 dark:text-red-400')}>
      {text}
    </p>
  );
}

function Divider() {
  return <div className="h-px bg-[#E5E5EA] dark:bg-[#38383A] my-8" />;
}

function Card({ children }: { children: React.ReactNode }) {
  return (
    <div className="rounded-2xl border border-[#E5E5EA] dark:border-[#38383A] p-5 space-y-4">
      {children}
    </div>
  );
}

export function SettingsPanel() {
  const { apiKey, userRole, darkMode, toggleDarkMode, clearAuth, activeMatterId, setActiveMatter, setView } =
    useStore();
  const qc = useQueryClient();

  // ── Projects ─────────────────────────────────────────────────────────────────
  const { data: mattersData } = useQuery<MattersResponse>({
    queryKey: ['matters'],
    queryFn: async () => {
      const r = await apiFetch<MattersResponse>('/api/matters', {}, apiKey ?? '');
      return r.data ?? { matters: [] };
    },
    staleTime: 30_000,
  });
  const matters = mattersData?.matters ?? [];

  // ── Create project ────────────────────────────────────────────────────────────
  const [newMatterName, setNewMatterName] = useState('');
  const [matterMsg, setMatterMsg] = useState<{ ok: boolean; text: string } | null>(null);

  const createMatter = useMutation({
    mutationFn: (name: string) =>
      apiFetch(`/api/matters?name=${encodeURIComponent(name)}`, { method: 'POST' }, apiKey ?? ''),
    onSuccess: (res) => {
      if (res.status === 200) {
        setNewMatterName('');
        setMatterMsg({ ok: true, text: 'Project created.' });
        qc.invalidateQueries({ queryKey: ['matters'] });
      } else if (res.status === 409) {
        setMatterMsg({ ok: false, text: 'A project with that name already exists.' });
      } else {
        setMatterMsg({ ok: false, text: res.error ?? 'Failed.' });
      }
    },
  });

  // ── Close project ────────────────────────────────────────────────────────────
  const [closeSel, setCloseSel] = useState('');
  const [closeConfirm, setCloseConfirm] = useState('');
  const [closeMsg, setCloseMsg] = useState<{ ok: boolean; text: string } | null>(null);
  const selectedMatterName = matters.find((m) => m.id === closeSel)?.name ?? '';

  const closeMatter = useMutation({
    mutationFn: (id: string) =>
      apiFetch<{ deleted_points: number }>(`/api/matters/${id}/close`, { method: 'POST' }, apiKey ?? ''),
    onSuccess: (res) => {
      if (res.status === 200) {
        const deleted = res.data?.deleted_points ?? 0;
        setCloseMsg({ ok: true, text: `Closed. ${deleted} records removed.` });
        setCloseConfirm('');
        if (activeMatterId === closeSel) setActiveMatter(null, 'All memories');
        qc.invalidateQueries({ queryKey: ['matters'] });
      } else {
        setCloseMsg({ ok: false, text: res.error ?? 'Failed.' });
      }
    },
  });

  // ── Single memory delete ──────────────────────────────────────────────────────
  const [delId, setDelId] = useState('');
  const [delConfirmed, setDelConfirmed] = useState(false);
  const [delMsg, setDelMsg] = useState<{ ok: boolean; text: string } | null>(null);

  const deleteSingle = useMutation({
    mutationFn: (id: string) =>
      apiFetch(`/api/memory/${id}`, { method: 'DELETE' }, apiKey ?? ''),
    onSuccess: (res) => {
      if (res.status === 200) {
        setDelId('');
        setDelConfirmed(false);
        setDelMsg({ ok: true, text: 'Memory deleted.' });
      } else if (res.status === 404) {
        setDelMsg({ ok: false, text: 'Memory not found.' });
      } else if (res.status === 403) {
        setDelMsg({ ok: false, text: 'Access denied.' });
      } else {
        setDelMsg({ ok: false, text: res.error ?? 'Failed.' });
      }
    },
  });

  // ── Batch delete ──────────────────────────────────────────────────────────────
  const [batchMatterSel, setBatchMatterSel] = useState('');
  const [batchType, setBatchType] = useState('all');
  const [batchConfirm, setBatchConfirm] = useState('');
  const [batchMsg, setBatchMsg] = useState<{ ok: boolean; text: string } | null>(null);
  const batchMatterName = matters.find((m) => m.id === batchMatterSel)?.name ?? '';

  const deleteBatch = useMutation({
    mutationFn: ({ matterId, type }: { matterId: string; type: string }) => {
      const params = new URLSearchParams({ matter_id: matterId });
      if (type !== 'all') params.set('type', type);
      return apiFetch(`/api/memories?${params.toString()}`, { method: 'DELETE' }, apiKey ?? '');
    },
    onSuccess: (res) => {
      if (res.status === 200) {
        setBatchConfirm('');
        setBatchMsg({ ok: true, text: 'Batch deleted.' });
      } else {
        setBatchMsg({ ok: false, text: res.error ?? 'Failed.' });
      }
    },
  });

  // ── Admin: users ──────────────────────────────────────────────────────────────
  const [newUserName, setNewUserName] = useState('');
  const [newUserRole, setNewUserRole] = useState('user');
  const [userMsg, setUserMsg] = useState<{ ok: boolean; text: string; key?: string } | null>(null);

  const { data: usersData } = useQuery<UsersResponse>({
    queryKey: ['users'],
    enabled: userRole === 'admin',
    queryFn: async () => {
      const r = await apiFetch<UsersResponse>('/api/users', {}, apiKey ?? '');
      return r.data ?? { users: [] };
    },
    staleTime: 60_000,
  });

  const createUser = useMutation({
    mutationFn: ({ name, role }: { name: string; role: string }) =>
      apiFetch<CreateUserResponse>(
        '/api/users',
        { method: 'POST', body: JSON.stringify({ display_name: name, role }) },
        apiKey ?? ''
      ),
    onSuccess: (res) => {
      if (res.status === 200 && res.data) {
        setNewUserName('');
        setUserMsg({ ok: true, text: `Created '${res.data.display_name}'.`, key: res.data.api_key });
        qc.invalidateQueries({ queryKey: ['users'] });
      } else {
        setUserMsg({ ok: false, text: res.error ?? 'Failed.' });
      }
    },
  });

  return (
    <div className="flex flex-col h-full bg-white dark:bg-[#121212]">
      {/* Header */}
      <div className="flex-shrink-0 flex items-center gap-3 px-5 py-3 border-b border-[#E5E5EA] dark:border-[#38383A]">
        <button
          onClick={() => setView('chat')}
          className="p-1 rounded-lg text-[#8E8E93] hover:text-[#1C1C1E] dark:hover:text-[#ECECEC] hover:bg-[#F2F2F7] dark:hover:bg-[#2C2C2E] transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
        </button>
        <h1 className="text-sm font-semibold text-[#1C1C1E] dark:text-[#ECECEC]">Settings</h1>
      </div>

      <div className="flex-1 overflow-y-auto">
        <div className="max-w-[620px] mx-auto px-6 py-8">

          {/* Appearance */}
          <SectionLabel>Appearance</SectionLabel>
          <Card>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-[#1C1C1E] dark:text-[#ECECEC]">Theme</p>
                <p className="text-xs text-[#8E8E93] mt-0.5">
                  {darkMode ? 'Dark mode active' : 'Light mode active'}
                </p>
              </div>
              <button
                onClick={toggleDarkMode}
                className="flex items-center gap-2 px-3 py-1.5 rounded-lg border border-[#E5E5EA] dark:border-[#38383A] text-sm text-[#1C1C1E] dark:text-[#ECECEC] hover:bg-[#F2F2F7] dark:hover:bg-[#2C2C2E] transition-colors"
              >
                {darkMode ? <Sun className="w-3.5 h-3.5" /> : <Moon className="w-3.5 h-3.5" />}
                {darkMode ? 'Light' : 'Dark'}
              </button>
            </div>
          </Card>

          <Divider />

          {/* Projects */}
          <SectionLabel>Projects</SectionLabel>
          <Card>
            <Field label="Create a new project">
              <div className="flex gap-2">
                <TextInput
                  value={newMatterName}
                  onChange={(e) => setNewMatterName(e.target.value)}
                  placeholder="e.g. Work Tasks, Reading List"
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && newMatterName.trim()) createMatter.mutate(newMatterName.trim());
                  }}
                  className="flex-1"
                />
                <Btn
                  variant="primary"
                  onClick={() => newMatterName.trim() && createMatter.mutate(newMatterName.trim())}
                  disabled={!newMatterName.trim() || createMatter.isPending}
                >
                  {createMatter.isPending ? 'Creating...' : 'Create'}
                </Btn>
              </div>
              {matterMsg && <StatusMsg {...matterMsg} />}
            </Field>

            {matters.length > 0 && (
              <Field label="Close a project">
                <SelectInput
                  value={closeSel}
                  onChange={(v) => { setCloseSel(v); setCloseMsg(null); }}
                  options={[
                    { value: '', label: 'Select a project...' },
                    ...matters.map((m) => ({ value: m.id, label: m.name })),
                  ]}
                />
                <TextInput
                  value={closeConfirm}
                  onChange={(e) => setCloseConfirm(e.target.value)}
                  placeholder={selectedMatterName ? `Type "${selectedMatterName}" to confirm` : 'Select a matter first'}
                />
                <Btn
                  variant="danger"
                  onClick={() => closeSel && closeMatter.mutate(closeSel)}
                  disabled={!closeSel || closeConfirm !== selectedMatterName || closeMatter.isPending}
                >
                  {closeMatter.isPending ? 'Closing...' : 'Close project'}
                </Btn>
                {closeMsg && <StatusMsg {...closeMsg} />}
              </Field>
            )}
          </Card>

          <Divider />

          {/* Memory */}
          <SectionLabel>Memory</SectionLabel>
          <Card>
            <Field label="Delete a single memory">
              <TextInput
                value={delId}
                onChange={(e) => setDelId(e.target.value)}
                placeholder="Point ID (UUID)"
              />
              <label className="flex items-center gap-2 text-xs text-[#8E8E93] cursor-pointer select-none">
                <input
                  type="checkbox"
                  checked={delConfirmed}
                  onChange={(e) => setDelConfirmed(e.target.checked)}
                  className="accent-red-500"
                />
                I understand this cannot be undone
              </label>
              <Btn
                variant="danger"
                onClick={() => delId.trim() && deleteSingle.mutate(delId.trim())}
                disabled={!delId.trim() || !delConfirmed || deleteSingle.isPending}
              >
                {deleteSingle.isPending ? 'Deleting...' : 'Delete memory'}
              </Btn>
              {delMsg && <StatusMsg {...delMsg} />}
            </Field>

            {matters.length > 0 && (
              <Field label="Batch delete by project">
                <SelectInput
                  value={batchMatterSel}
                  onChange={(v) => { setBatchMatterSel(v); setBatchMsg(null); }}
                  options={[
                    { value: '', label: 'Select a project...' },
                    ...matters.map((m) => ({ value: m.id, label: m.name })),
                  ]}
                />
                <SelectInput
                  value={batchType}
                  onChange={setBatchType}
                  options={[
                    { value: 'all', label: 'All types' },
                    { value: 'file_ingest', label: 'File ingest' },
                    { value: 'raw_ingestion', label: 'Raw ingestion' },
                    { value: 'browsing_event', label: 'Browsing event' },
                    { value: 'explicit_memory', label: 'Explicit memory' },
                  ]}
                />
                <TextInput
                  value={batchConfirm}
                  onChange={(e) => setBatchConfirm(e.target.value)}
                  placeholder={batchMatterName ? `Type "${batchMatterName}" to confirm` : 'Select a matter first'}
                />
                <Btn
                  variant="danger"
                  onClick={() =>
                    batchMatterSel && deleteBatch.mutate({ matterId: batchMatterSel, type: batchType })
                  }
                  disabled={!batchMatterSel || batchConfirm !== batchMatterName || deleteBatch.isPending}
                >
                  {deleteBatch.isPending ? 'Deleting...' : 'Delete all'}
                </Btn>
                {batchMsg && <StatusMsg {...batchMsg} />}
              </Field>
            )}
          </Card>

          {/* Admin: users */}
          {userRole === 'admin' && (
            <>
              <Divider />
              <SectionLabel>Users</SectionLabel>
              <Card>
                <Field label="Create a new user">
                  <div className="flex gap-2">
                    <TextInput
                      value={newUserName}
                      onChange={(e) => setNewUserName(e.target.value)}
                      placeholder="Display name"
                      className="flex-1"
                    />
                    <SelectInput
                      value={newUserRole}
                      onChange={setNewUserRole}
                      options={[
                        { value: 'user', label: 'User' },
                        { value: 'admin', label: 'Admin' },
                      ]}
                    />
                  </div>
                  <Btn
                    variant="primary"
                    onClick={() =>
                      newUserName.trim() && createUser.mutate({ name: newUserName.trim(), role: newUserRole })
                    }
                    disabled={!newUserName.trim() || createUser.isPending}
                  >
                    {createUser.isPending ? 'Creating...' : 'Create user'}
                  </Btn>
                  {userMsg && (
                    <div className="space-y-1.5">
                      <StatusMsg ok={userMsg.ok} text={userMsg.text} />
                      {userMsg.key && (
                        <>
                          <code className="block text-xs font-mono text-[#1C1C1E] dark:text-[#ECECEC] bg-[#F2F2F7] dark:bg-[#1C1C1E] border border-[#E5E5EA] dark:border-[#38383A] p-3 rounded-lg break-all leading-relaxed">
                            {userMsg.key}
                          </code>
                          <p className="text-xs text-[#8E8E93]">API key shown once only. Copy and store it now.</p>
                        </>
                      )}
                    </div>
                  )}
                </Field>

                {usersData && usersData.users.length > 0 && (
                  <div className="border-t border-[#E5E5EA] dark:border-[#38383A] pt-4 space-y-2">
                    {usersData.users.map((u) => (
                      <div key={u.user_id} className="flex items-center justify-between">
                        <span className="text-sm text-[#1C1C1E] dark:text-[#ECECEC]">{u.display_name}</span>
                        <span className="text-xs text-[#8E8E93] capitalize">{u.role}</span>
                      </div>
                    ))}
                  </div>
                )}
              </Card>
            </>
          )}

          <Divider />

          {/* Account */}
          <SectionLabel>Account</SectionLabel>
          <Card>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-[#1C1C1E] dark:text-[#ECECEC]">Disconnect</p>
                <p className="text-xs text-[#8E8E93] mt-0.5">Clear API key and return to login</p>
              </div>
              <Btn variant="danger" onClick={clearAuth}>
                <span className="flex items-center gap-1.5">
                  <LogOut className="w-3.5 h-3.5" />
                  Disconnect
                </span>
              </Btn>
            </div>
          </Card>

          <div className="h-8" />
        </div>
      </div>
    </div>
  );
}
