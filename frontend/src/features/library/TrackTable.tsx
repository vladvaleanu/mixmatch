import type { CSSProperties } from 'react';

import type { Schemas } from '../../api/client';
import { useSetEnergy } from '../../api/tracks';
import { ro } from '../../i18n/ro';
import { color, coverColor, fontSize, radius, space } from '../../theme/tokens';
import { formatBpm, formatDuration } from '../../ui/format';
import { EnergyDots } from '../../ui/EnergyDots';
import { KeyPill } from '../../ui/KeyPill';
import { Waveform } from '../../ui/Waveform';
import { useSelectedTrack } from './selectionStore';
import { TrackPlayButton } from './TrackPlayButton';

type Track = Schemas['TrackOut'];
type Props = { tracks: Track[] };

const cell = { padding: `${space[10]}px ${space[8]}px` } satisfies CSSProperties;
const firstCell = { ...cell, paddingLeft: space[16] } satisfies CSSProperties;
const lastCell = { ...cell, paddingRight: space[16] } satisfies CSSProperties;
const numeric = { fontVariantNumeric: 'tabular-nums' } satisfies CSSProperties;
const visuallyHidden = {
  position: 'absolute',
  width: 1,
  height: 1,
  overflow: 'hidden',
  clip: 'rect(0 0 0 0)',
} satisfies CSSProperties;

const th = {
  ...cell,
  paddingTop: space[12],
  paddingBottom: space[12],
  fontWeight: 500,
  fontSize: fontSize.label,
  color: color.textMuted,
  textAlign: 'left',
  whiteSpace: 'nowrap',
} satisfies CSSProperties;

function Pending() {
  return (
    <span aria-label={ro.analysis.pending} style={{ color: color.textMuted }}>
      …
    </span>
  );
}

export function TrackTable({ tracks }: Props) {
  const setEnergy = useSetEnergy();
  const { id: selectedId, select } = useSelectedTrack();
  return (
    <div
      style={{
        overflowX: 'auto',
        borderRadius: radius.card,
        background: color.surface,
        border: `1px solid ${color.border}`,
      }}
    >
      <table style={{ width: '100%', minWidth: 860, borderCollapse: 'collapse' }}>
        <thead>
          <tr>
            <th scope="col" style={{ ...th, paddingLeft: space[16], width: 1 }}>
              <span style={visuallyHidden}>{ro.library.columns.play}</span>
            </th>
            <th scope="col" style={th}>
              {ro.library.columns.track}
            </th>
            <th scope="col" style={{ ...th, width: 1 }}>
              {ro.library.columns.bpm}
            </th>
            <th scope="col" style={{ ...th, width: 1 }}>
              {ro.library.columns.key}
            </th>
            <th scope="col" style={{ ...th, width: 1 }}>
              {ro.library.columns.energy}
            </th>
            <th scope="col" style={{ ...th, width: 1 }}>
              {ro.library.columns.duration}
            </th>
            <th scope="col" style={{ ...th, paddingRight: space[16], width: 1 }}>
              {ro.library.columns.waveform}
            </th>
          </tr>
        </thead>
        <tbody>
          {tracks.map((track) => (
            <tr
              key={track.id}
              onClick={() => select(track.id)}
              aria-selected={track.id === selectedId}
              style={{
                borderTop: `1px solid ${color.border}`,
                background: track.id === selectedId ? color.surface3 : 'transparent',
                cursor: 'pointer',
              }}
            >
              <td style={firstCell}>
                <TrackPlayButton track={track} />
              </td>
              <td style={cell}>
                <span style={{ display: 'flex', alignItems: 'center', gap: space[12] }}>
                  <span
                    aria-hidden="true"
                    style={{
                      flex: '0 0 32px',
                      width: 32,
                      height: 32,
                      borderRadius: radius.pill,
                      background: coverColor(track.key_camelot),
                    }}
                  />
                  <span style={{ display: 'flex', flexDirection: 'column', gap: 2, minWidth: 0 }}>
                    <button
                      type="button"
                      onClick={() => select(track.id)}
                      style={{
                        all: 'unset',
                        fontWeight: 500,
                        cursor: 'pointer',
                      }}
                    >
                      {track.title}
                    </button>
                    <span style={{ color: color.textMuted, fontSize: fontSize.meta }}>
                      {track.artist ?? ro.library.unknownArtist}
                    </span>
                  </span>
                </span>
              </td>
              <td style={{ ...cell, ...numeric }}>
                {track.bpm !== null ? formatBpm(track.bpm) : !track.analyzed && <Pending />}
              </td>
              <td style={cell}>
                {track.key_camelot ? (
                  <KeyPill code={track.key_camelot} name={track.key_name} />
                ) : (
                  !track.analyzed && <Pending />
                )}
              </td>
              <td style={cell}>
                {track.energy !== null ? (
                  <EnergyDots
                    value={track.energy}
                    manual={track.energy_manual !== null}
                    onChange={(energy) => setEnergy.mutate({ id: track.id, energy })}
                  />
                ) : (
                  !track.analyzed && <Pending />
                )}
              </td>
              <td style={{ ...cell, ...numeric, color: color.textSoft }}>
                {formatDuration(track.duration_s)}
              </td>
              <td style={lastCell}>
                {track.waveform_preview && <Waveform peaks={track.waveform_preview} height={28} />}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
