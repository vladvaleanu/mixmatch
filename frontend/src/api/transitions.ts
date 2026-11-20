import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { http, unwrap, type Schemas } from './client';

const transitionKey = (mixId: number, position: number) =>
  ['mixes', mixId, 'transitions', position] as const;

/** Tranziția dintre pozițiile `position − 1` și `position`, cu planul ei. */
export function useTransition(mixId: number, position: number) {
  return useQuery({
    queryKey: transitionKey(mixId, position),
    queryFn: () =>
      unwrap(
        http.GET('/api/mixes/{mix_id}/transitions/{position}/plan', {
          params: { path: { mix_id: mixId, position } },
        }),
      ),
    placeholderData: (previous) => previous,
  });
}

export function useUpdateTransition(mixId: number, position: number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: Schemas['TransitionPatch']) =>
      unwrap(
        http.PATCH('/api/mixes/{mix_id}/transitions/{position}', {
          params: { path: { mix_id: mixId, position } },
          body,
        }),
      ),
    onSuccess: (out) => queryClient.setQueryData(transitionKey(mixId, position), out),
  });
}
