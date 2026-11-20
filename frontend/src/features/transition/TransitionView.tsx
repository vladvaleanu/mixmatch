import type { Schemas } from '../../api/client';
import { valueAt } from '../../audio/plan';
import { useWaveform } from '../../api/tracks';
import { ro } from '../../i18n/ro';
import { color, fontSize, space } from '../../theme/tokens';

type Transition = Schemas['TransitionOut'];
type Plan = Schemas['PlanOut'];
type Automation = Plan['automations'][number];

// Fereastra = de 4 ori lungimea tranziției: A ocupă ~80 %, suprapunerea începe la ~55 % (machetă).
const BEFORE = 2.2;
const AFTER = 1.8;
const LANE_H = 64;
const LINES_H = 72;
const BARS = 180;
const BASS_RANGE_DB = 26;

/** Bare din vârfurile `hi` pe intervalul [fromS, toS] al fișierului. */
function slice(
  peaks: number[],
  duration: number,
  fromS: number,
  toS: number,
  bars: number,
): (number | null)[] {
  return Array.from({ length: bars }, (_, i) => {
    const t0 = fromS + ((toS - fromS) * i) / bars;
    const t1 = fromS + ((toS - fromS) * (i + 1)) / bars;
    if (t1 <= 0 || t0 >= duration) return null;
    const a = Math.max(0, Math.floor((t0 / duration) * peaks.length));
    const b = Math.min(peaks.length, Math.max(a + 1, Math.ceil((t1 / duration) * peaks.length)));
    return Math.max(...peaks.slice(a, b));
  });
}

function Lane({ values, fill, label }: { values: (number | null)[]; fill: string; label: string }) {
  const w = 1000 / values.length;
  return (
    <div style={{ position: 'relative', display: 'flex', flexDirection: 'column', gap: space[6] }}>
      <span style={{ fontSize: fontSize.label, color: color.textMuted }}>{label}</span>
      <svg
        viewBox={`0 0 1000 ${LANE_H}`}
        preserveAspectRatio="none"
        aria-hidden="true"
        style={{ width: '100%', height: LANE_H, display: 'block' }}
      >
        {values.map((v, i) => {
          if (v === null) return null;
          const h = Math.max(2, (v / 255) * LANE_H);
          return (
            <rect
              key={i}
              x={i * w + w * 0.2}
              y={(LANE_H - h) / 2}
              width={w * 0.6}
              height={h}
              rx={1}
              fill={fill}
            />
          );
        })}
      </svg>
    </div>
  );
}

export function TransitionView({
  transition,
  playheadT,
}: {
  transition: Transition;
  /** Momentul redat acum (timpul tranziției), pentru cursor. */
  playheadT: number | null;
}) {
  const { plan, from_track: a, to_track: b } = transition;
  const waveA = useWaveform(a.id, 'hi').data?.peaks;
  const waveB = useWaveform(b.id, 'hi').data?.peaks;
  const L = plan.length_s;
  const start = -BEFORE * L;
  const end = AFTER * L;
  const x = (t: number) => ((t - start) / (end - start)) * 1000;
  const bAudible = (plan.b_in_s - plan.b_start_s) / plan.speed_b; // când devine B audibilă

  // A: din fereastră până la finalul tranziției; B: de când se aude până la finalul ferestrei.
  const barsA = Math.round((BARS * (L - start)) / (end - start));
  const barsB = Math.round((BARS * (end - bAudible)) / (end - start));
  const laneA = waveA
    ? slice(waveA, a.duration_s, plan.a_start_s + start, plan.a_start_s + L, barsA)
    : [];
  const laneB = waveB
    ? slice(waveB, b.duration_s, plan.b_in_s, plan.b_start_s + end * plan.speed_b, barsB)
    : [];

  const line = (auto: Automation, map: (v: number) => number) => {
    const ts = [start, ...auto.points.map((p) => p.t_s), end];
    return ts
      .map((t, i) => {
        // Pentru salturi (două puncte la același t) folosim valoarea punctului respectiv.
        const point = auto.points[i - 1];
        const v = point && i > 0 && i < ts.length - 1 ? point.value : valueAt(auto.points, t);
        return `${x(t)},${LINES_H - 6 - map(v) * (LINES_H - 12)}`;
      })
      .join(' ');
  };
  const style: Record<Automation['target'], { stroke: string; dash?: string; label: string }> = {
    a_volume: { stroke: color.textSoft, label: ro.transitionEditor.lines.a_volume },
    b_volume: { stroke: color.accent, label: ro.transitionEditor.lines.b_volume },
    a_bass: { stroke: color.info, dash: '6 5', label: ro.transitionEditor.lines.bass },
    b_bass: { stroke: color.info, dash: '6 5', label: ro.transitionEditor.lines.bass },
    a_echo: { stroke: color.warn, dash: '2 4', label: ro.transitionEditor.lines.a_echo },
  };
  const toUnit = (target: Automation['target']) =>
    target.endsWith('bass') ? (v: number) => 1 + v / BASS_RANGE_DB : (v: number) => v;
  const legend = [
    ...new Map(plan.automations.map((a) => [style[a.target].label, style[a.target]])).values(),
  ];

  return (
    <section
      aria-label={ro.transitionEditor.overlapLabel}
      style={{
        position: 'relative',
        borderRadius: 16,
        background: color.surface,
        border: `1px solid ${color.border}`,
        padding: `${space[28]}px ${space[24]}px ${space[20]}px`,
        display: 'flex',
        flexDirection: 'column',
        gap: space[18],
        overflow: 'hidden',
      }}
    >
      <div
        style={{ position: 'relative', display: 'flex', flexDirection: 'column', gap: space[18] }}
      >
        <div
          aria-hidden="true"
          style={{
            position: 'absolute',
            top: -space[20],
            bottom: 0,
            left: `${x(0) / 10}%`,
            width: `${(x(L) - x(0)) / 10}%`,
            background: color.accentTint,
            borderLeft: `2px solid ${color.accent}`,
            borderRight: `2px solid ${color.accent}`,
          }}
        />
        <span
          style={{
            position: 'absolute',
            top: -space[20],
            left: `calc(${x(0) / 10}% + ${space[10]}px)`,
            fontSize: fontSize.label,
            color: color.accentSoftText,
            fontWeight: 600,
          }}
        >
          {ro.transitionEditor.overlap(plan.length_bars, Math.round(L))}
        </span>
        {playheadT !== null && (
          <div
            aria-hidden="true"
            style={{
              position: 'absolute',
              top: -space[20],
              bottom: 0,
              left: `${x(playheadT) / 10}%`,
              width: 2,
              background: color.text,
              zIndex: 1,
            }}
          />
        )}
        <div style={{ width: `${x(L) / 10}%` }}>
          <Lane values={laneA} fill={color.waveIdle} label={ro.transitionEditor.deckA(a.title)} />
        </div>
        <div style={{ marginLeft: `${x(bAudible) / 10}%` }}>
          <Lane values={laneB} fill={color.accent} label={ro.transitionEditor.deckB(b.title)} />
        </div>
        <svg
          viewBox={`0 0 1000 ${LINES_H}`}
          preserveAspectRatio="none"
          role="img"
          aria-label={ro.transitionEditor.automationLabel}
          style={{ width: '100%', height: LINES_H, display: 'block' }}
        >
          {plan.automations.map((auto) => (
            <polyline
              key={auto.target}
              points={line(auto, toUnit(auto.target))}
              fill="none"
              stroke={style[auto.target].stroke}
              strokeWidth="2"
              strokeDasharray={style[auto.target].dash}
              vectorEffect="non-scaling-stroke"
            />
          ))}
        </svg>
      </div>
      <div
        style={{
          display: 'flex',
          flexWrap: 'wrap',
          gap: space[18],
          fontSize: fontSize.label,
          color: color.textSoft,
        }}
      >
        {legend.map((l) => (
          <span key={l.label} style={{ display: 'flex', alignItems: 'center', gap: space[8] }}>
            <svg width="16" height="4" aria-hidden="true">
              <line
                x1="0"
                y1="2"
                x2="16"
                y2="2"
                stroke={l.stroke}
                strokeWidth="2"
                strokeDasharray={l.dash}
              />
            </svg>
            {l.label}
          </span>
        ))}
      </div>
    </section>
  );
}
