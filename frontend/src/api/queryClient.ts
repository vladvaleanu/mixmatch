import { MutationCache, QueryCache, QueryClient } from '@tanstack/react-query';

import { showToast } from '../ui/toastStore';

declare module '@tanstack/react-query' {
  interface Register {
    queryMeta: { silent?: boolean };
  }
}

/** Orice eroare de la API ajunge în toast-ul global, în afară de cererile marcate `silent`. */
export function createQueryClient(): QueryClient {
  const report = (error: Error) => showToast(error.message);
  return new QueryClient({
    queryCache: new QueryCache({
      onError: (error, query) => {
        if (!query.meta?.silent) report(error);
      },
    }),
    mutationCache: new MutationCache({ onError: report }),
  });
}
