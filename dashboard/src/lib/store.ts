import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export type View = 'chat' | 'agents' | 'memories' | 'settings';

export interface MessageSource {
  memory: string;
  score: number;
  classification?: string;
}

export interface ChatMessage {
  role: 'user' | 'engram';
  text: string;
  time: string;
  classification?: string;
  sources?: MessageSource[];
}

interface AppState {
  // null  = never authenticated (show auth screen)
  // ''    = authenticated in dev mode (no key required)
  // str   = authenticated with a real API key
  apiKey: string | null;
  userRole: string;
  setAuth: (apiKey: string, role: string) => void;
  clearAuth: () => void;

  view: View;
  setView: (v: View) => void;

  darkMode: boolean;
  toggleDarkMode: () => void;

  activeMatterId: string | null;
  activeMatterName: string;
  setActiveMatter: (id: string | null, name: string) => void;

  selectedModel: string;
  setSelectedModel: (model: string) => void;

  messages: ChatMessage[];
  addMessage: (msg: ChatMessage) => void;
  updateLastMessage: (delta: string, classification?: string, sources?: MessageSource[]) => void;
  clearMessages: () => void;
}

export const useStore = create<AppState>()(
  persist(
    (set) => ({
      apiKey: null,
      userRole: 'user',
      setAuth: (apiKey, userRole) => set({ apiKey, userRole }),
      clearAuth: () => set({ apiKey: null, userRole: 'user', messages: [] }),

      view: 'chat',
      setView: (view) => set({ view }),

      darkMode: true,
      toggleDarkMode: () => set((s) => ({ darkMode: !s.darkMode })),

      activeMatterId: null,
      activeMatterName: 'All memories',
      setActiveMatter: (activeMatterId, activeMatterName) =>
        set({ activeMatterId, activeMatterName }),

      selectedModel: '',
      setSelectedModel: (selectedModel) => set({ selectedModel }),

      messages: [],
      addMessage: (msg) => set((s) => ({ messages: [...s.messages, msg] })),
      updateLastMessage: (delta, classification, sources) =>
        set((s) => {
          const msgs = [...s.messages];
          const last = msgs[msgs.length - 1];
          if (!last || last.role !== 'engram') return s;
          msgs[msgs.length - 1] = {
            ...last,
            text: last.text + delta,
            ...(classification !== undefined ? { classification } : {}),
            ...(sources !== undefined ? { sources } : {}),
          };
          return { messages: msgs };
        }),
      clearMessages: () => set({ messages: [] }),
    }),
    {
      name: 'engram-dashboard',
      partialize: (s) => ({
        apiKey: s.apiKey,
        userRole: s.userRole,
        darkMode: s.darkMode,
        activeMatterId: s.activeMatterId,
        activeMatterName: s.activeMatterName,
        selectedModel: s.selectedModel,
        messages: s.messages.slice(-100),
      }),
    }
  )
);
