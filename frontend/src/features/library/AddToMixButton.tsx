import type { Schemas } from '../../api/client';
import { useCreateMix, useMix, useMixes, useSetMixItems } from '../../api/mixes';
import { ro } from '../../i18n/ro';
import { color, radius, size, space } from '../../theme/tokens';
import { Button } from '../../ui/Button';
import { PlusIcon } from '../../ui/PlusIcon';
import { useActiveMix } from '../mix-builder/activeMixStore';

/** „Adaugă în mix” din panoul piesei: în mixul activ (ultimul deschis) sau într-unul nou. */
export function AddToMixButton({ track }: { track: Schemas['TrackOut'] }) {
  const mixes = useMixes();
  const { id: activeId, setId } = useActiveMix();
  // Mixul activ, dacă mai există; altfel cel mai recent modificat.
  const targetId = mixes.data?.find((m) => m.id === activeId)?.id ?? mixes.data?.[0]?.id ?? null;
  const target = useMix(targetId);
  const setItems = useSetMixItems(targetId ?? 0);
  const create = useCreateMix();

  if (!mixes.data) return null;

  if (targetId === null) {
    return (
      <Button
        variant="primary"
        disabled={create.isPending}
        onClick={() =>
          create.mutate(
            { name: ro.mixes.defaultName, track_ids: [track.id] },
            { onSuccess: (mix) => setId(mix.id) },
          )
        }
      >
        <PlusIcon />
        {ro.addToMix.addNew}
      </Button>
    );
  }

  const name = target.data?.name ?? '';
  const already = target.data?.tracks.some((t) => t.id === track.id) ?? false;
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: space[8] }}>
      <Button
        variant="primary"
        disabled={!target.data || already || setItems.isPending}
        onClick={() => target.data && setItems.mutate([...target.data.tracks, track])}
      >
        {!already && <PlusIcon />}
        {already ? ro.addToMix.already(name) : ro.addToMix.add(name)}
      </Button>
      {mixes.data.length > 1 && (
        <select
          aria-label={ro.addToMix.target}
          value={targetId}
          onChange={(event) => setId(Number(event.target.value))}
          style={{
            height: size.touch,
            padding: `0 ${space[10]}px`,
            borderRadius: radius.control,
            border: `1px solid ${color.borderStrong}`,
            background: color.surface2,
            color: color.textSoft,
            font: 'inherit',
          }}
        >
          {mixes.data.map((mix) => (
            <option key={mix.id} value={mix.id}>
              {mix.name}
            </option>
          ))}
        </select>
      )}
    </div>
  );
}
