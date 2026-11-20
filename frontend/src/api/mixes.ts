import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { http, unwrap, type Schemas } from './client';

export const mixesKey = ['mixes'] as const;
const mixKey = (id: number) => [...mixesKey, id] as const;
const reportKey = (id: number) => [...mixesKey, id, 'report'] as const;

type Mix = Schemas['MixOut'];

export function useMixes() {
  return useQuery({
    queryKey: mixesKey,
    queryFn: () => unwrap(http.GET('/api/mixes')),
  });
}

export function useMix(mixId: number | null) {
  return useQuery({
    queryKey: mixKey(mixId ?? 0),
    queryFn: () =>
      unwrap(http.GET('/api/mixes/{mix_id}', { params: { path: { mix_id: mixId ?? 0 } } })),
    enabled: mixId !== null,
  });
}

/** După orice schimbare: detaliul vine din răspuns, lista și raportul se reîncarcă. */
function useSaved() {
  const queryClient = useQueryClient();
  return (mix: Mix) => {
    queryClient.setQueryData(mixKey(mix.id), mix);
    void queryClient.invalidateQueries({ queryKey: mixesKey, exact: true });
    void queryClient.invalidateQueries({ queryKey: reportKey(mix.id) });
  };
}

/** Etichetele tranzițiilor, curba de energie și avertismentele, calculate de server. */
export function useMixReport(mixId: number) {
  return useQuery({
    queryKey: reportKey(mixId),
    queryFn: () =>
      unwrap(http.GET('/api/mixes/{mix_id}/report', { params: { path: { mix_id: mixId } } })),
    placeholderData: (previous) => previous, // fără clipire cât se recalculează
  });
}

export function useSetEnergyShape(mixId: number) {
  const saved = useSaved();
  return useMutation({
    mutationFn: (energy_shape: Mix['energy_shape']) =>
      unwrap(
        http.PATCH('/api/mixes/{mix_id}', {
          params: { path: { mix_id: mixId } },
          body: { energy_shape },
        }),
      ),
    onSuccess: saved,
  });
}

export function useCreateMix() {
  const saved = useSaved();
  return useMutation({
    mutationFn: (body: Schemas['MixCreate']) => unwrap(http.POST('/api/mixes', { body })),
    onSuccess: saved,
  });
}

export function useRenameMix(mixId: number) {
  const saved = useSaved();
  return useMutation({
    mutationFn: (name: string) =>
      unwrap(
        http.PATCH('/api/mixes/{mix_id}', { params: { path: { mix_id: mixId } }, body: { name } }),
      ),
    onSuccess: saved,
  });
}

export function useDeleteMix() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (mixId: number) => {
      // 204 fără corp: verificăm doar răspunsul.
      const { response, error } = await http.DELETE('/api/mixes/{mix_id}', {
        params: { path: { mix_id: mixId } },
      });
      if (!response.ok) await unwrap(Promise.resolve({ error, response }));
      return mixId;
    },
    onSuccess: (mixId) => {
      queryClient.removeQueries({ queryKey: mixKey(mixId) });
      void queryClient.invalidateQueries({ queryKey: mixesKey, exact: true });
    },
  });
}

/** Ordinea completă a pieselor. Interfața se actualizează imediat; serverul confirmă. */
export function useSetMixItems(mixId: number) {
  const queryClient = useQueryClient();
  const saved = useSaved();
  return useMutation({
    mutationFn: (tracks: Mix['tracks']) =>
      unwrap(
        http.PUT('/api/mixes/{mix_id}/items', {
          params: { path: { mix_id: mixId } },
          body: { track_ids: tracks.map((t) => t.id) },
        }),
      ),
    onMutate: (tracks) => {
      const previous = queryClient.getQueryData<Mix>(mixKey(mixId));
      if (previous) queryClient.setQueryData(mixKey(mixId), { ...previous, tracks });
      return { previous };
    },
    onError: (_error, _tracks, context) => {
      if (context?.previous) queryClient.setQueryData(mixKey(mixId), context.previous);
    },
    onSuccess: saved,
  });
}
