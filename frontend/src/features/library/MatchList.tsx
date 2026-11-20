import { useMatches } from '../../api/tracks';
import type { Schemas } from '../../api/client';
import { ro } from '../../i18n/ro';
import { color, coverColor, fontSize, radius, space } from '../../theme/tokens';
import { TransitionTag } from '../../ui/TransitionTag';
import { useSelectedTrack } from './selectionStore';

/** „Merg bine după ea”: sugestiile calculate de backend pentru piesa selectată. */
export function MatchList({ track }: { track: Schemas['TrackOut'] }) {
  const matches = useMatches(track.analyzed ? track.id : null);
  const select = useSelectedTrack((s) => s.select);

  const note = (text: string) => <p style={{ margin: 0, color: color.textMuted }}>{text}</p>;

  return (
    <section style={{ display: 'flex', flexDirection: 'column', gap: space[10] }}>
      <h2
        style={{
          margin: 0,
          fontSize: fontSize.label,
          fontWeight: 600,
          letterSpacing: '0.06em',
          textTransform: 'uppercase',
          color: color.textMuted,
        }}
      >
        {ro.matches.title}
      </h2>
      {!track.analyzed
        ? note(ro.matches.notAnalyzed)
        : matches.data?.length === 0
          ? note(ro.matches.empty)
          : matches.data?.map((m) => (
              <button
                key={m.track.id}
                type="button"
                onClick={() => select(m.track.id)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: space[12],
                  padding: space[8],
                  margin: -space[8],
                  border: 0,
                  borderRadius: radius.control,
                  background: 'transparent',
                  color: color.text,
                  font: 'inherit',
                  textAlign: 'left',
                  cursor: 'pointer',
                }}
              >
                <span
                  aria-hidden="true"
                  style={{
                    flex: '0 0 36px',
                    height: 36,
                    borderRadius: radius.pill,
                    background: coverColor(m.track.key_camelot),
                  }}
                />
                <span
                  style={{ flex: 1, minWidth: 0, display: 'flex', flexDirection: 'column', gap: 2 }}
                >
                  <span
                    style={{
                      fontWeight: 500,
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      whiteSpace: 'nowrap',
                    }}
                  >
                    {m.track.title}
                  </span>
                  <span style={{ color: color.textMuted, fontSize: fontSize.meta }}>
                    {m.reason}
                  </span>
                </span>
                <TransitionTag label={m.label} />
              </button>
            ))}
    </section>
  );
}
