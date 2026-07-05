import { useRef, useEffect, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { ArrowUp, ChevronDown } from 'lucide-react';
import { apiFetch } from '../lib/api';
import { useStore, type ChatMessage, type MessageSource } from '../lib/store';
import { cn } from '../lib/cn';

interface ModelsResponse {
  models: Array<{ name: string }>;
}

interface ChatResponse {
  reply: string;
  context_used?: Array<{
    memory: string;
    score: number;
    classification?: string;
  }>;
}

const CLF_RANK: Record<string, number> = {
  PUBLIC: 0, INTERNAL: 1, CONFIDENTIAL: 2, PRIVILEGED: 3, PHI: 4, PII: 5, RESTRICTED: 6,
};

const SUGGESTIONS = [
  'What did I save recently?',
  'What do you know about me?',
  'What’s on my calendar this week?',
];

function greeting(): string {
  const h = new Date().getHours();
  if (h < 5) return 'Up late';
  if (h < 12) return 'Good morning';
  if (h < 17) return 'Good afternoon';
  return 'Good evening';
}

function ClassificationBadge({ clf }: { clf?: string }) {
  if (!clf) return null;
  if (['PHI', 'PII', 'RESTRICTED'].includes(clf)) {
    return (
      <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[9px] font-bold tracking-widest uppercase bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400 ml-2">
        {clf}
      </span>
    );
  }
  if (clf === 'CONFIDENTIAL') {
    return (
      <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[9px] font-bold tracking-widest uppercase bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400 ml-2">
        {clf}
      </span>
    );
  }
  return null;
}

// Mirrors the backend's URL stripping — sources are stored raw, cleaned only for display.
function cleanSourceText(text: string): string {
  return text.replace(/\(?https?:\/\/\S+\)?/g, '').replace(/\s{2,}/g, ' ').trim();
}

function SourcesDisclosure({ sources }: { sources: MessageSource[] }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="mt-2">
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center gap-1 text-[11px] text-[#8E8E93] hover:text-[#1C1C1E] dark:hover:text-[#ECECEC] transition-colors"
      >
        <ChevronDown className={cn('w-3 h-3 transition-transform', open && 'rotate-180')} />
        {sources.length} {sources.length === 1 ? 'memory' : 'memories'} used
      </button>
      {open && (
        <div className="mt-2 rounded-xl border border-[#E5E5EA] dark:border-[#38383A] bg-[#FAFAFA] dark:bg-[#1C1C1E] divide-y divide-[#E5E5EA] dark:divide-[#38383A] animate-fade-in">
          {sources.map((s, i) => (
            <div key={i} className="px-3 py-2.5 flex items-start gap-2">
              <span className="flex-shrink-0 mt-0.5 text-[10px] tabular-nums text-[#8E8E93] w-8">
                {Math.round(s.score * 100)}%
              </span>
              <p className="flex-1 min-w-0 text-xs leading-relaxed text-[#48484A] dark:text-[#AEAEB2] line-clamp-3">
                {cleanSourceText(s.memory)}
                <ClassificationBadge clf={s.classification} />
              </p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function MessageBubble({ msg }: { msg: ChatMessage }) {
  if (msg.role === 'user') {
    return (
      <div className="flex justify-end mb-6 animate-fade-up">
        <div className="max-w-[72%]">
          <div className="px-4 py-3 rounded-2xl rounded-br-md bg-[#F2F2F7] dark:bg-[#2C2C2E] text-sm leading-relaxed text-[#1C1C1E] dark:text-[#ECECEC] whitespace-pre-wrap">
            {msg.text}
          </div>
          <div className="text-right mt-1">
            <span className="text-[10px] text-[#8E8E93]">{msg.time}</span>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex items-start gap-3 mb-6 animate-fade-up">
      <div className="w-7 h-7 rounded-full bg-gradient-to-br from-accent-400 to-accent-600 flex items-center justify-center flex-shrink-0 mt-0.5">
        <span className="text-[9px] font-bold text-white">E</span>
      </div>
      <div className="flex-1 min-w-0">
        <div className="text-sm leading-[1.8] text-[#1C1C1E] dark:text-[#ECECEC] whitespace-pre-wrap">
          {msg.text}
        </div>
        <div className="mt-1 flex items-center">
          <span className="text-[10px] text-[#8E8E93]">{msg.time}</span>
          <ClassificationBadge clf={msg.classification} />
        </div>
        {msg.sources && msg.sources.length > 0 && (
          <SourcesDisclosure sources={msg.sources} />
        )}
      </div>
    </div>
  );
}

function ThinkingBubble() {
  return (
    <div className="flex items-start gap-3 mb-6 animate-fade-in">
      <div className="w-7 h-7 rounded-full bg-gradient-to-br from-accent-400 to-accent-600 flex items-center justify-center flex-shrink-0 mt-0.5">
        <span className="text-[9px] font-bold text-white">E</span>
      </div>
      <div className="flex items-center gap-1.5 py-1.5">
        {[0, 120, 240].map((delay) => (
          <span
            key={delay}
            className="w-1.5 h-1.5 rounded-full bg-accent-400 animate-bounce"
            style={{ animationDelay: `${delay}ms` }}
          />
        ))}
      </div>
    </div>
  );
}

function InputCard({
  value,
  onChange,
  onSend,
  onKeyDown,
  onInput,
  disabled,
  textareaRef,
  models,
  selectedModel,
  onModelChange,
}: {
  value: string;
  onChange: (v: string) => void;
  onSend: () => void;
  onKeyDown: (e: React.KeyboardEvent<HTMLTextAreaElement>) => void;
  onInput: (e: React.FormEvent<HTMLTextAreaElement>) => void;
  disabled: boolean;
  textareaRef: React.RefObject<HTMLTextAreaElement>;
  models: Array<{ name: string }>;
  selectedModel: string;
  onModelChange: (m: string) => void;
}) {
  const canAct = !!value.trim() && !disabled;
  return (
    <div className="w-full max-w-[680px] mx-auto px-4">
      {/* Single-row composer: controls flank the textarea, bottom-aligned so
          the text grows upward while buttons stay pinned. */}
      <div className="flex items-end gap-2 rounded-2xl border border-[#E5E5EA] dark:border-[#38383A] bg-white dark:bg-[#1C1C1E] shadow-sm pl-4 pr-2 py-2 transition-colors focus-within:border-accent-300 dark:focus-within:border-accent-700">
        <textarea
          ref={textareaRef}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={onKeyDown}
          onInput={onInput}
          placeholder="Ask Engram..."
          rows={1}
          className="flex-1 min-w-0 py-1.5 text-sm bg-transparent outline-none resize-none leading-relaxed text-[#1C1C1E] dark:text-[#ECECEC] placeholder:text-[#8E8E93]"
          style={{ maxHeight: 180, overflowY: 'auto' }}
        />
        {models.length > 0 && (
          /* Invisible-select overlay: the visible pill sizes to the *selected*
             value, while the transparent native select on top keeps the real
             dropdown. A bare <select> would size to its longest option,
             leaving dead space before the chevron. */
          <div
            className="relative flex-shrink-0 mb-0.5 flex items-center gap-1 px-2 py-1.5 rounded-lg text-xs text-[#8E8E93] hover:bg-[#F2F2F7] dark:hover:bg-[#2C2C2E] hover:text-[#1C1C1E] dark:hover:text-[#ECECEC] transition-colors"
            title="Model"
          >
            <span className="truncate max-w-[120px]">{selectedModel || 'Default'}</span>
            <ChevronDown className="w-3 h-3 flex-shrink-0" />
            <select
              value={selectedModel}
              onChange={(e) => onModelChange(e.target.value)}
              className="absolute inset-0 w-full opacity-0 cursor-pointer"
              aria-label="Model"
            >
              <option value="">Default</option>
              {models.map((m) => (
                <option key={m.name} value={m.name}>{m.name}</option>
              ))}
            </select>
          </div>
        )}
        <button
          onClick={onSend}
          disabled={!canAct}
          title="Send (Enter)"
          className={cn(
            'flex-shrink-0 w-7 h-7 mb-0.5 rounded-full flex items-center justify-center transition-all active:scale-90',
            'bg-accent-500 hover:bg-accent-600',
            !canAct && 'opacity-25 cursor-not-allowed hover:bg-accent-500'
          )}
        >
          <ArrowUp className="w-3.5 h-3.5 text-white" />
        </button>
      </div>
      <p className="text-center text-[10px] text-[#8E8E93] mt-2">
        Enter to send · Shift+Enter for new line
      </p>
    </div>
  );
}

export function Chat() {
  const {
    apiKey, activeMatterId, activeMatterName,
    messages, addMessage, updateLastMessage, clearMessages, setView,
    selectedModel, setSelectedModel,
  } = useStore();

  const { data: modelsData } = useQuery<ModelsResponse>({
    queryKey: ['models'],
    queryFn: async () => {
      const r = await apiFetch<ModelsResponse>('/api/models', {}, apiKey ?? '');
      return r.data ?? { models: [] };
    },
    staleTime: 60_000,
  });
  const models = modelsData?.models ?? [];
  const [input, setInput] = useState('');
  const [sending, setSending] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, sending]);

  const matterPayload = activeMatterId ? { matter_id: activeMatterId } : {};
  const hasMessages = messages.length > 0;

  function now() {
    return new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  }

  function resetTextarea() {
    setInput('');
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  }

  async function handleSend() {
    const text = input.trim();
    if (!text || sending) return;
    resetTextarea();
    addMessage({ role: 'user', text, time: now() });
    setSending(true);

    try {
      const headers: Record<string, string> = { 'Content-Type': 'application/json' };
      if (apiKey) headers['X-API-Key'] = apiKey;

      const response = await fetch('/chat', {
        method: 'POST',
        headers,
        body: JSON.stringify({
          text,
          stream: true,
          ...matterPayload,
          ...(selectedModel && { model: selectedModel }),
        }),
      });

      if (!response.ok || !response.body) {
        addMessage({
          role: 'engram',
          text: response.ok ? 'Something went wrong.' : `Error ${response.status}.`,
          time: now(),
        });
        return;
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      let engramAdded = false;

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        // SSE events are separated by double newlines
        const parts = buffer.split('\n\n');
        buffer = parts.pop() ?? '';

        for (const part of parts) {
          for (const line of part.split('\n')) {
            if (!line.startsWith('data: ')) continue;
            try {
              const data = JSON.parse(line.slice(6)) as {
                delta: string;
                done: boolean;
                context_used?: MessageSource[];
              };
              if (data.done) {
                if (!engramAdded) {
                  addMessage({ role: 'engram', text: '(no response)', time: now() });
                  engramAdded = true;
                }
                const contexts = data.context_used ?? [];
                const topClf = contexts
                  .map((c) => c.classification ?? 'PUBLIC')
                  .reduce((best, c) => (CLF_RANK[c] ?? 0) > (CLF_RANK[best] ?? 0) ? c : best, '');
                updateLastMessage('', topClf || undefined, contexts);
              } else if (data.delta) {
                if (!engramAdded) {
                  addMessage({ role: 'engram', text: data.delta, time: now() });
                  engramAdded = true;
                } else {
                  updateLastMessage(data.delta);
                }
              }
            } catch {
              // malformed chunk — skip
            }
          }
        }
      }
    } finally {
      setSending(false);
    }
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }

  function handleInput(e: React.FormEvent<HTMLTextAreaElement>) {
    const el = e.currentTarget;
    el.style.height = 'auto';
    el.style.height = Math.min(el.scrollHeight, 180) + 'px';
  }

  const inputCard = (
    <InputCard
      value={input}
      onChange={setInput}
      onSend={handleSend}
      onKeyDown={handleKeyDown}
      onInput={handleInput}
      disabled={sending}
      textareaRef={textareaRef}
      models={models}
      selectedModel={selectedModel}
      onModelChange={setSelectedModel}
    />
  );

  return (
    <div className="flex flex-col h-full bg-white dark:bg-[#121212]">
      {/* Top bar */}
      <div className="flex-shrink-0 flex items-center justify-between px-5 py-3 border-b border-[#E5E5EA] dark:border-[#38383A]">
        <button
          onClick={() => setView('settings')}
          className="flex items-center gap-1 text-sm font-medium text-[#1C1C1E] dark:text-[#ECECEC] hover:opacity-60 transition-opacity"
        >
          {activeMatterName}
          <ChevronDown className="w-3.5 h-3.5 text-[#8E8E93]" />
        </button>
        {hasMessages && (
          <button
            onClick={clearMessages}
            className="text-xs text-[#8E8E93] hover:text-[#1C1C1E] dark:hover:text-[#ECECEC] transition-colors"
          >
            Clear
          </button>
        )}
      </div>

      {/* Content area */}
      {!hasMessages ? (
        /* Empty state — center the prompt + input */
        <div className="flex-1 flex flex-col items-center justify-center pb-10 gap-7 animate-fade-up">
          <div className="text-center">
            <p className="text-2xl font-medium tracking-tight">
              <span className="text-accent-500">{greeting()}.</span>{' '}
              <span className="text-[#1C1C1E] dark:text-[#ECECEC]">What should I remember?</span>
            </p>
            <p className="text-sm text-[#8E8E93] mt-1.5">
              Everything you tell me stays on this machine.
            </p>
          </div>
          {inputCard}
          <div className="flex flex-wrap items-center justify-center gap-2 px-4 max-w-[680px]">
            {SUGGESTIONS.map((s) => (
              <button
                key={s}
                onClick={() => {
                  setInput(s);
                  textareaRef.current?.focus();
                }}
                className="px-3.5 py-1.5 rounded-full border border-[#E5E5EA] dark:border-[#38383A] text-xs text-[#8E8E93] hover:text-[#1C1C1E] dark:hover:text-[#ECECEC] hover:border-accent-300 dark:hover:border-accent-700 hover:bg-accent-50 dark:hover:bg-accent-500/10 transition-colors active:scale-95"
              >
                {s}
              </button>
            ))}
          </div>
        </div>
      ) : (
        /* Messages + bottom input */
        <>
          <div className="flex-1 overflow-y-auto">
            <div className="max-w-[680px] mx-auto px-4 py-8">
              {messages.map((msg, i) => (
                <MessageBubble key={i} msg={msg} />
              ))}
              {sending && messages[messages.length - 1]?.role !== 'engram' && <ThinkingBubble />}
              <div ref={bottomRef} />
            </div>
          </div>
          <div className="flex-shrink-0 pb-6 pt-2">
            {inputCard}
          </div>
        </>
      )}
    </div>
  );
}
