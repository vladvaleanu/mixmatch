import { create } from 'zustand';

/** Dacă dialogul „Adaugă folder” e deschis. Butonul din bara de sus îl deschide de oriunde. */
export const useAddFolderDialog = create<{ open: boolean; setOpen: (open: boolean) => void }>(
  (set) => ({ open: false, setOpen: (open) => set({ open }) }),
);
