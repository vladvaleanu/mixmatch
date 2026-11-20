import { create } from 'zustand';

import type { TrackFilters } from '../../api/tracks';

type FilterState = {
  filters: TrackFilters;
  set: (patch: Partial<TrackFilters>) => void;
  reset: () => void;
};

export const emptyFilters: TrackFilters = {
  q: '',
  bpm_min: null,
  bpm_max: null,
  energy: [],
  key: [],
  compatible_with: null,
  sort: 'title',
};

/** Filtrele Bibliotecii (bara laterală, căutarea din bara de sus, sortarea). */
export const useFilters = create<FilterState>((set) => ({
  filters: emptyFilters,
  set: (patch) => set((state) => ({ filters: { ...state.filters, ...patch } })),
  reset: () => set((state) => ({ filters: { ...emptyFilters, sort: state.filters.sort } })),
}));

export function hasActiveFilters(f: TrackFilters): boolean {
  return Boolean(
    f.q.trim() ||
    f.bpm_min !== null ||
    f.bpm_max !== null ||
    f.energy.length ||
    f.key.length ||
    f.compatible_with !== null,
  );
}
