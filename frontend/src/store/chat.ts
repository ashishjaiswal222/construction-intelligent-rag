import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { ChatMessageData } from '@/components/chat/ChatMessage';

export interface ChatSession {
  id: string;
  projectId: string;
  title: string;
  messages: ChatMessageData[];
  createdAt: number;
  updatedAt: number;
}

interface ChatState {
  sessions: ChatSession[];
  activeSessionId: string | null;
  
  // Actions
  setActiveSession: (id: string | null) => void;
  createSession: (projectId: string, title?: string) => string;
  deleteSession: (id: string) => void;
  updateSessionMessages: (id: string, messages: ChatMessageData[]) => void;
  updateSessionTitle: (id: string, title: string) => void;
  getSessionsForProject: (projectId: string) => ChatSession[];
}

export const useChatStore = create<ChatState>()(
  persist(
    (set, get) => ({
      sessions: [],
      activeSessionId: null,

      setActiveSession: (id) => set({ activeSessionId: id }),

      createSession: (projectId, title = 'New Chat') => {
        const id = Date.now().toString();
        const newSession: ChatSession = {
          id,
          projectId,
          title,
          messages: [],
          createdAt: Date.now(),
          updatedAt: Date.now(),
        };

        set((state) => ({
          sessions: [newSession, ...state.sessions],
          activeSessionId: id,
        }));

        return id;
      },

      deleteSession: (id) => set((state) => {
        const newSessions = state.sessions.filter(s => s.id !== id);
        return {
          sessions: newSessions,
          activeSessionId: state.activeSessionId === id ? null : state.activeSessionId
        };
      }),

      updateSessionMessages: (id, messages) => set((state) => ({
        sessions: state.sessions.map(s => 
          s.id === id 
            ? { ...s, messages, updatedAt: Date.now() } 
            : s
        )
      })),

      updateSessionTitle: (id, title) => set((state) => ({
        sessions: state.sessions.map(s => 
          s.id === id 
            ? { ...s, title, updatedAt: Date.now() } 
            : s
        )
      })),

      getSessionsForProject: (projectId) => {
        return get().sessions.filter(s => s.projectId === projectId);
      }
    }),
    {
      name: 'cip-chat-storage', // name of the item in the storage (must be unique)
    }
  )
);
