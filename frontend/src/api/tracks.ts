import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { http, unwrap, type Schemas } from './client';

export const tracksKey = ['tracks'] as const;

export function useTracks() {
  return useQuery({
    queryKey: tracksKey,
    queryFn: () => unwrap(http.GET('/api/tracks')),
  });
}

/** Corectura manuală a energiei; null = revino la energia automată. */
export function useSetEnergy() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, energy }: { id: number; energy: number | null }) =>
      unwrap(
        http.PATCH('/api/tracks/{track_id}', {
          params: { path: { track_id: id } },
          body: { energy_manual: energy },
        }),
      ),
    // Tabelul primește piesa așa cum o întoarce serverul (energia efectivă e calculată acolo).
    onSuccess: (updated) => {
      queryClient.setQueryData<Schemas['TrackOut'][]>(tracksKey, (tracks) =>
        tracks?.map((track) => (track.id === updated.id ? updated : track)),
      );
    },
  });
}
