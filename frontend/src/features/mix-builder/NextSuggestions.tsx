import type { ReactNode } from 'react';

import type { Schemas } from '../../api/client';
import { useMatches } from '../../api/tracks';
import { ro } from '../../i18n/ro';
import { color, coverColor, fontSize, radius, space } from '../../theme/tokens';
import { PlusIcon } from '../../ui/PlusIcon';
import { TransitionTag } from '../../ui/TransitionTag';

type Props = {
  mix: Schemas['MixOut'];
  nextTargetEnergy: number | null;
  onAdd: (track: Schemas['TrackOut']) => void;
};

function Legend() {
  const row = (mark: ReactNode, text: string) => (
    <span style={{ display: 'flex', alignItems: 'center', gap: space[10], color: color.textSoft }}>
      {mark}
      {text}
    </span>
  );
  const dot = (bg: string, r: number, rotate = 0) => (
    <span
      aria-hidden="true"
      style={{
        width: 10,
        height: 10,
        flex: 'none',
        borderRadius: r,
        background: bg,
        transform: `rotate(${rotate}deg)`,
      }}
    />
  );
  return (
    <div
      style={{
        marginTop: space[8],
        padding: space[16],
        borderRadius: radius.card,
        border: `1px solid ${color.border}`,
        display: 'flex',
        flexDirection: 'column',
        gap: space[10],
      }}
    >
      <span style={{ fontWeight: 600 }}>{ro.report.legend}</span>
      {row(dot(color.accent, radius.round), ro.report.legendSmooth)}
      {row(dot(color.info, 3), ro.report.legendGood)}
      {row(dot(color.warn, 2, 45), ro.report.legendCaution)}
    </div>
  );
}

/** „Ce urmează după …”: sugestii după ultima piesă, fără piesele din mix, după curba aleasă. */
export function NextSuggestions({ mix, nextTargetEnergy, onAdd }: Props) {
  const last = mix.tracks[mix.tracks.length - 1];
  const matches = useMatches(last?.analyzed ? last.id : null, {
    exclude_mix: mix.id,
    target_energy: nextTargetEnergy ?? undefined,
  });

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: space[18] }}>
      <div>
        <h2 style={{ margin: 0, fontSize: 15, fontWeight: 600 }}>
          {last ? ro.report.next(last.title) : ro.report.nextEmpty}
        </h2>
        <p
          style={{
            margin: `${space[4]}px 0 0`,
            color: color.textMuted,
            fontSize: fontSize.meta,
            lineHeight: 1.5,
          }}
        >
          {last ? ro.report.nextHint : ro.report.nextStart}
        </p>
      </div>
      {last && matches.data?.length === 0 && (
        <p style={{ margin: 0, color: color.textMuted }}>{ro.report.nextNone}</p>
      )}
      {matches.data?.slice(0, 5).map((m) => (
        <div
          key={m.track.id}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: space[12],
            padding: space[12],
            borderRadius: radius.control,
            background: color.surface2,
          }}
        >
          <span
            aria-hidden="true"
            style={{
              flex: '0 0 40px',
              height: 40,
              borderRadius: radius.buttonSm,
              background: coverColor(m.track.key_camelot),
            }}
          />
          <span style={{ flex: 1, minWidth: 0, display: 'flex', flexDirection: 'column', gap: 2 }}>
            <span style={{ fontWeight: 500, overflowWrap: 'anywhere' }}>{m.track.title}</span>
            <span style={{ color: color.textMuted, fontSize: fontSize.meta }}>{m.reason}</span>
            <span>
              <TransitionTag label={m.label} />
            </span>
          </span>
          <button
            type="button"
            aria-label={ro.report.addSuggestion(m.track.title)}
            onClick={() => onAdd(m.track)}
            style={{
              width: 40,
              height: 40,
              flex: 'none',
              borderRadius: radius.buttonSm,
              border: 0,
              background: color.control,
              color: color.text,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              cursor: 'pointer',
            }}
          >
            <PlusIcon />
          </button>
        </div>
      ))}
      <Legend />
    </div>
  );
}
