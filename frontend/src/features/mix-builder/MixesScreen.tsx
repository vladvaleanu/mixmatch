import { Link, useNavigate } from 'react-router-dom';

import { useCreateMix, useMixes } from '../../api/mixes';
import { ro } from '../../i18n/ro';
import { color, font, fontSize, radius, space } from '../../theme/tokens';
import { Button } from '../../ui/Button';
import { formatMinutes } from '../../ui/format';
import { PlusIcon } from '../../ui/PlusIcon';
import { ScreenHeader } from '../../ui/ScreenHeader';
import { useActiveMix } from './activeMixStore';

const dateFormat = new Intl.DateTimeFormat('ro-RO', { day: 'numeric', month: 'short' });

const card = {
  minHeight: 132,
  padding: space[18],
  borderRadius: radius.card,
  display: 'flex',
  flexDirection: 'column',
  gap: space[8],
  textDecoration: 'none',
} as const;

export function MixesScreen() {
  const mixes = useMixes();
  const create = useCreateMix();
  const setActive = useActiveMix((s) => s.setId);
  const navigate = useNavigate();

  const createMix = () =>
    create.mutate(
      { name: ro.mixes.defaultName, track_ids: [] },
      {
        onSuccess: (mix) => {
          setActive(mix.id);
          navigate(`/mixuri/${mix.id}`);
        },
      },
    );

  return (
    <div
      style={{
        flex: 1,
        padding: space[28],
        display: 'flex',
        flexDirection: 'column',
        gap: space[24],
      }}
    >
      <div
        style={{
          display: 'flex',
          flexWrap: 'wrap',
          alignItems: 'flex-end',
          justifyContent: 'space-between',
          gap: space[12],
        }}
      >
        <ScreenHeader title={ro.mixes.title} subtitle={ro.mixes.subtitle} />
        <Button variant="primary" onClick={createMix} disabled={create.isPending}>
          <PlusIcon />
          {ro.mixes.create}
        </Button>
      </div>

      {mixes.isPending ? (
        <p style={{ margin: 0, color: color.textMuted }}>{ro.mixes.loading}</p>
      ) : (
        <ul
          style={{
            listStyle: 'none',
            margin: 0,
            padding: 0,
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fill, minmax(240px, 1fr))',
            gap: space[16],
          }}
        >
          {mixes.data?.map((mix) => (
            <li key={mix.id} style={{ display: 'flex' }}>
              <Link
                to={`/mixuri/${mix.id}`}
                style={{
                  ...card,
                  flex: 1,
                  background: color.surface,
                  border: `1px solid ${color.border}`,
                  color: color.text,
                }}
              >
                <span style={{ fontFamily: font.display, fontSize: 20, fontWeight: 600 }}>
                  {mix.name}
                </span>
                <span style={{ color: color.textSoft }}>
                  {ro.mixes.meta(mix.track_count, formatMinutes(mix.duration_s))}
                </span>
                <span
                  style={{ marginTop: 'auto', color: color.textMuted, fontSize: fontSize.meta }}
                >
                  {ro.mixes.updated(dateFormat.format(new Date(mix.updated_at)))}
                </span>
              </Link>
            </li>
          ))}
          {mixes.data?.length === 0 && (
            <li style={{ display: 'flex' }}>
              <button
                type="button"
                onClick={createMix}
                style={{
                  ...card,
                  flex: 1,
                  alignItems: 'center',
                  justifyContent: 'center',
                  border: `1.5px dashed ${color.borderDashed}`,
                  background: 'transparent',
                  color: color.textMuted,
                  font: 'inherit',
                  cursor: 'pointer',
                }}
              >
                <PlusIcon />
                {ro.mixes.createFirst}
              </button>
            </li>
          )}
        </ul>
      )}
    </div>
  );
}
