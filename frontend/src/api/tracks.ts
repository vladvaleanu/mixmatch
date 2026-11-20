import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import type { paths } from './schema';
import { http, unwrap, type Schemas } from './client';

export const tracksKey = ['tracks'] as const;
const matchesKey = ['matches'] as const;

type ListQuery = NonNullable<paths['/api/tracks']['get']['parameters']['query']>;

/** Filtrele din UI; câmpurile goale nu se trimit. */
export type TrackFilters = {
  q: string;
  bpm_min: number | null;
  bpm_max: number | null;
  energy: number[];
  key: string[];
  compatible_with: number | null;
  collection: number | null; // colecția aleasă în bara laterală
  sort: NonNullable<ListQuery['sort']>;
};

function toQuery(f: TrackFilters): ListQuery {
  return {
    q: f.q.trim() || undefined,
    bpm_min: f.bpm_min ?? undefined,
    bpm_max: f.bpm_max ?? undefined,
    energy: f.energy.length ? f.energy : undefined,
    key: f.key.length ? f.key : undefined,
    compatible_with: f.compatible_with ?? undefined,
    collection: f.collection ?? undefined,
    sort: f.sort,
  };
}

/** Biblioteca. Fără filtre: toate piesele (de ex. pentru numărul total). */
export function useTracks(filters?: TrackFilters) {
  return useQuery({
    queryKey: [...tracksKey, filters ?? null],
    queryFn: () =>
      unwrap(http.GET('/api/tracks', { params: { query: filters ? toQuery(filters) : {} } })),
    placeholderData: (previous) => previous, // tabelul nu clipește când se schimbă filtrele
  });
}

type MatchQuery = NonNullable<
  paths['/api/tracks/{track_id}/matches']['get']['parameters']['query']
>;

/** „Merg bine după ea”: sugestiile pentru piesa dată, cele mai bune primele.
 *  În Constructor: fără piesele mixului și după energia dorită de curbă. */
export function useMatches(trackId: number | null, options: MatchQuery = {}) {
  return useQuery({
    queryKey: [...matchesKey, trackId, options],
    queryFn: () =>
      unwrap(
        http.GET('/api/tracks/{track_id}/matches', {
          params: { path: { track_id: trackId ?? 0 }, query: options },
        }),
      ),
    enabled: trackId !== null,
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
      queryClient.setQueriesData<Schemas['TrackOut'][]>({ queryKey: tracksKey }, (tracks) =>
        tracks?.map((track) => (track.id === updated.id ? updated : track)),
      );
      // Energia schimbă și filtrele și sugestiile: le recalculează serverul.
      void queryClient.invalidateQueries({ queryKey: tracksKey });
      void queryClient.invalidateQueries({ queryKey: matchesKey });
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

/** O bucată de audio (WAV) dintr-o piesă, pentru previzualizarea tranzițiilor. */
export async function fetchClip(
  trackId: number,
  startS: number,
  endS: number,
): Promise<ArrayBuffer> {
  const { data, error, response } = await http.GET('/api/tracks/{track_id}/clip', {
    params: { path: { track_id: trackId }, query: { start_s: startS, end_s: endS } },
    parseAs: 'arrayBuffer',
  });
  if (data === undefined) await unwrap(Promise.resolve({ error, response }));
  return data as ArrayBuffer;
}
