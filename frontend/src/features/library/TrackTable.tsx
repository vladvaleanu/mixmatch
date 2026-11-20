import type { Schemas } from '../../api/client';
import { ro } from '../../i18n/ro';
import { color, fontSize, radius, space } from '../../theme/tokens';
import { formatDuration } from '../../ui/format';

type Props = { tracks: Schemas['TrackOut'][] };

const th = {
  padding: `${space[12]}px ${space[8]}px`,
  fontWeight: 500,
  fontSize: fontSize.label,
  color: color.textMuted,
  textAlign: 'left',
} as const;

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
      <table style={{ width: '100%', borderCollapse: 'collapse' }}>
        <thead>
          <tr>
            <th scope="col" style={{ ...th, paddingLeft: space[16] }}>
              {ro.library.columns.track}
            </th>
            <th scope="col" style={{ ...th, paddingRight: space[16], width: 1 }}>
              {ro.library.columns.duration}
            </th>
          </tr>
        </thead>
        <tbody>
          {tracks.map((track) => (
            <tr key={track.id} style={{ borderTop: `1px solid ${color.border}` }}>
              <td style={{ padding: `${space[10]}px ${space[8]}px ${space[10]}px ${space[16]}px` }}>
                <span style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                  <span style={{ fontWeight: 500 }}>{track.title}</span>
                  <span style={{ color: color.textMuted, fontSize: fontSize.meta }}>
                    {track.artist ?? ro.library.unknownArtist}
                  </span>
                </span>
              </td>
              <td
                style={{
                  padding: `${space[10]}px ${space[16]}px ${space[10]}px ${space[8]}px`,
                  color: color.textSoft,
                  fontVariantNumeric: 'tabular-nums',
                }}
              >
                {formatDuration(track.duration_s)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
