import { useQuery } from '@tanstack/react-query';

import { http, unwrap } from './client';

const POLL_MS = 500;
const ACTIVE_POLL_MS = 1500;

export const activeJobsKey = ['jobs', 'active'] as const;

/** Starea unui job; se reîmprospătează până când jobul se termină. */
export function useJob(jobId: number | null) {
  return useQuery({
    queryKey: ['jobs', jobId],
    queryFn: () =>
      unwrap(http.GET('/api/jobs/{job_id}', { params: { path: { job_id: jobId ?? 0 } } })),
    enabled: jobId !== null,
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      return status === 'done' || status === 'failed' ? false : POLL_MS;
    },
  });
}

/** Joburile în lucru. Se reîmprospătează cât timp există vreunul; altfel doar la invalidare. */
export function useActiveJobs() {
  return useQuery({
    queryKey: activeJobsKey,
    queryFn: () => unwrap(http.GET('/api/jobs/active')),
    refetchInterval: (query) => (query.state.data?.length ? ACTIVE_POLL_MS : false),
  });
}
