import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { http, unwrap } from './client';
import { tracksKey } from './tracks';

const collectionsKey = ['collections'] as const;

export function useCollections() {
  return useQuery({
    queryKey: collectionsKey,
    queryFn: () => unwrap(http.GET('/api/collections')),
  });
}

function useRefresh() {
  const queryClient = useQueryClient();
  return () => {
    void queryClient.invalidateQueries({ queryKey: collectionsKey });
    void queryClient.invalidateQueries({ queryKey: tracksKey });
  };
}

export function useCreateCollection() {
  const refresh = useRefresh();
  return useMutation({
    mutationFn: (name: string) => unwrap(http.POST('/api/collections', { body: { name } })),
    onSuccess: refresh,
  });
}

export function useDeleteCollection() {
  const refresh = useRefresh();
  return useMutation({
    mutationFn: async (collectionId: number) => {
      const { response, error } = await http.DELETE('/api/collections/{collection_id}', {
        params: { path: { collection_id: collectionId } },
      });
      if (!response.ok) await unwrap(Promise.resolve({ error, response }));
    },
    onSuccess: refresh,
  });
}

/** Pune piesa în colecție sau o scoate. */
export function useToggleCollection() {
  const refresh = useRefresh();
  return useMutation({
    mutationFn: ({
      collectionId,
      trackId,
      member,
    }: {
      collectionId: number;
      trackId: number;
      member: boolean;
    }) => {
      const params = { params: { path: { collection_id: collectionId, track_id: trackId } } };
      return unwrap(
        member
          ? http.PUT('/api/collections/{collection_id}/tracks/{track_id}', params)
          : http.DELETE('/api/collections/{collection_id}/tracks/{track_id}', params),
      );
    },
    onSuccess: refresh,
  });
}
