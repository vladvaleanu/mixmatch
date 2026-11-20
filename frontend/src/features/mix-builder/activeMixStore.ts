import { create } from 'zustand';
import { persist } from 'zustand/middleware';

/** Mixul în care adaugă „Adaugă în mix” din Bibliotecă: ultimul deschis sau creat. */
export const useActiveMix = create<{ id: number | null; setId: (id: number | null) => void }>()(
  persist((set) => ({ id: null, setId: (id) => set({ id }) }), { name: 'mixmatch.activeMix' }),
);
