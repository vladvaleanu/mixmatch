import type { CSSProperties } from 'react';

import type { Schemas } from '../../api/client';
import { ro } from '../../i18n/ro';
import { color, coverColor, fontSize, radius, space } from '../../theme/tokens';
import { formatBpm, formatDuration } from '../../ui/format';
import { KeyPill } from '../../ui/KeyPill';

type Track = Schemas['TrackOut'];
type Props = { tracks: Track[] };

const cell = { padding: `${space[10]}px ${space[8]}px` } satisfies CSSProperties;
const firstCell = { ...cell, paddingLeft: space[16] } satisfies CSSProperties;
const lastCell = { ...cell, paddingRight: space[16] } satisfies CSSProperties;
const numeric = { fontVariantNumeric: 'tabular-nums' } satisfies CSSProperties;

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
  return (
    <div
      style={{
        overflowX: 'auto',
        borderRadius: radius.card,
        background: color.surface,
        border: `1px solid ${color.border}`,
      }}
    >
      <table style={{ width: '100%', minWidth: 560, borderCollapse: 'collapse' }}>
        <thead>
          <tr>
            <th scope="col" style={{ ...th, paddingLeft: space[16] }}>
              {ro.library.columns.track}
            </th>
            <th scope="col" style={{ ...th, width: 1 }}>
              {ro.library.columns.bpm}
            </th>
            <th scope="col" style={{ ...th, width: 1 }}>
              {ro.library.columns.key}
            </th>
            <th scope="col" style={{ ...th, paddingRight: space[16], width: 1 }}>
              {ro.library.columns.duration}
            </th>
          </tr>
        </thead>
        <tbody>
          {tracks.map((track) => (
            <tr key={track.id} style={{ borderTop: `1px solid ${color.border}` }}>
              <td style={firstCell}>
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
                    <span style={{ fontWeight: 500 }}>{track.title}</span>
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
              <td style={{ ...lastCell, ...numeric, color: color.textSoft }}>
                {formatDuration(track.duration_s)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
