import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import type { paths } from './schema';
import { http, unwrap } from './client';

const exportsKey = ['exports'] as const;
const POLL_MS = 1000;

type FileKind = NonNullable<
  NonNullable<paths['/api/exports/{export_id}/file']['get']['parameters']['query']>['kind']
>;

/** Pornește exportul mixului; urmărești jobul cu `useJob` sau în ecranul Exporturi. */
export function useExportMix(mixId: number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (format: 'wav' | 'mp3') =>
      unwrap(
        http.POST('/api/mixes/{mix_id}/export', {
          params: { path: { mix_id: mixId } },
          body: { format },
        }),
      ),
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: exportsKey }),
  });
}

/** Exporturile; se reîmprospătează cât timp unul încă se randează. */
export function useExports() {
  return useQuery({
    queryKey: exportsKey,
    queryFn: () => unwrap(http.GET('/api/exports')),
    refetchInterval: (query) =>
      query.state.data?.some((e) => e.job && ['queued', 'running'].includes(e.job.status))
        ? POLL_MS
        : false,
  });
}

const FILE_PATH = '/api/exports/{export_id}/file' satisfies keyof paths;

/** Adresa de descărcare a unui fișier din export (browserul o deschide direct). */
export function exportFileUrl(exportId: number, kind: FileKind): string {
  return `${FILE_PATH.replace('{export_id}', String(exportId))}?kind=${kind}`;
}
