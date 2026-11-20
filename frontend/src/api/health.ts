import { useQuery } from '@tanstack/react-query';

import { http, unwrap } from './client';

export function useHealth() {
  return useQuery({
    queryKey: ['health'],
    queryFn: () => unwrap(http.GET('/api/health')),
    refetchInterval: 10_000,
    retry: false,
    meta: { silent: true }, // starea serverului se vede în bara de sus, nu în toast
  });
}
