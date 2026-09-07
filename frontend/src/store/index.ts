import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { Project } from '@/types';

interface AppState {
  activeProject: Project | null;
  setActiveProject: (project: Project | null) => void;
  selectedDocId: string | null;
  setSelectedDocId: (docId: string | null) => void;
}

export const useAppStore = create<AppState>()(
  persist(
    (set) => ({
      activeProject: null,
      setActiveProject: (project) => set({ activeProject: project }),
      selectedDocId: null,
      setSelectedDocId: (docId) => set({ selectedDocId: docId }),
    }),
    {
      name: 'cip-app-storage',
    }
  )
);
