import { useQuery } from '@tanstack/react-query';

import { apiGet } from './client';

export function useHealth() {
  return useQuery({
    queryKey: ['health'],
    queryFn: () => apiGet('/api/health'),
    refetchInterval: 10_000,
    retry: false,
  });
}
