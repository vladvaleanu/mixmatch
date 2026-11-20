import { create } from 'zustand';

/** Piesa selectată în Bibliotecă (afișată în panoul din dreapta). */
export const useSelectedTrack = create<{ id: number | null; select: (id: number) => void }>(
  (set) => ({ id: null, select: (id) => set({ id }) }),
);
