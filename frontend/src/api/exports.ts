import { useMutation } from '@tanstack/react-query';

import { http, unwrap } from './client';

/** Pornește exportul mixului; urmărești jobul cu `useJob`. */
export function useExportMix(mixId: number) {
  return useMutation({
    mutationFn: (format: 'wav' | 'mp3') =>
      unwrap(
        http.POST('/api/mixes/{mix_id}/export', {
          params: { path: { mix_id: mixId } },
          body: { format },
        }),
      ),
  });
}
