import { useQuery } from '@tanstack/react-query';

import { http, unwrap } from './client';

export const tracksKey = ['tracks'] as const;

export function useTracks() {
  return useQuery({
    queryKey: tracksKey,
    queryFn: () => unwrap(http.GET('/api/tracks')),
  });
}
