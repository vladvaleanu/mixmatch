import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import type { paths } from './schema';
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

const AUDIO_PATH = '/api/tracks/{track_id}/audio' satisfies keyof paths;

/** Adresa fișierului audio, pentru player (elementul <audio> face singur cererile cu Range). */
export function trackAudioUrl(trackId: number): string {
  return AUDIO_PATH.replace('{track_id}', String(trackId));
}

export function useWaveform(trackId: number | null, res: 'lo' | 'hi' = 'lo') {
  return useQuery({
    queryKey: ['waveform', trackId, res],
    queryFn: () =>
      unwrap(
        http.GET('/api/tracks/{track_id}/waveform', {
          params: { path: { track_id: trackId ?? 0 }, query: { res } },
        }),
      ),
    enabled: trackId !== null,
    staleTime: Infinity, // se schimbă doar la reanaliză
    meta: { silent: true }, // fără formă de undă, panoul arată doar un loc gol
  });
}
