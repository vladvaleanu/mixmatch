import { useMutation } from '@tanstack/react-query';

import { http, unwrap } from './client';

export function useAddFolder() {
  return useMutation({
    mutationFn: (path: string) => unwrap(http.POST('/api/library/folders', { body: { path } })),
  });
}
