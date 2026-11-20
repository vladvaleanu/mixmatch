import { useEffect, type CSSProperties } from 'react';
import { Link, useParams } from 'react-router-dom';

import type { Schemas } from '../../api/client';
import { fetchClip } from '../../api/tracks';
import { useTransition, useUpdateTransition } from '../../api/transitions';
import { transitionPreview, usePreview } from '../../audio/engine';
import { ro } from '../../i18n/ro';
import { color, font, fontSize, radius, size, space } from '../../theme/tokens';
import { Button } from '../../ui/Button';
import { formatBpm, formatDuration } from '../../ui/format';
import { TransitionView } from './TransitionView';

type Transition = Schemas['TransitionOut'];
type Label = Transition['label'];
type Style = Schemas['PlanOut']['style'];

const LENGTHS = [8, 16, 32, 64] as const;
const STYLES: Style[] = ['eq_swap', 'crossfade', 'echo_out', 'cut'];
const PHRASE_BARS = 8;

const chipColors: Record<Label, CSSProperties> = {
  smooth: { background: color.accentSoftBg, color: color.accentSoftText },
  good: { background: color.infoSoftBg, color: color.infoSoftText },
  caution: { background: color.warnSoftBg, color: color.warnSoftText },
};

function Chip({ label, children }: { label: Label | null; children: string }) {
  return (
    <span
      style={{
        padding: `${space[8]}px ${space[12]}px`,
        borderRadius: radius.round,
        ...(label ? chipColors[label] : { background: color.surface2, color: color.textSoft }),
      }}
    >
      {children}
    </span>
  );
}

function Chips({ t }: { t: Transition }) {
  const a = t.from_track;
  const b = t.to_track;
  const e = ro.transitionEditor;
  const speedPct = (t.plan.speed_b - 1) * 100;
  const change =
    Math.abs(speedPct) < 0.05
      ? e.synced
      : e.speedB(`${speedPct > 0 ? '+' : '−'}${Math.abs(speedPct).toFixed(1).replace('.', ',')}`);
  const synced = t.key_after_sync !== b.key_camelot ? t.key_after_sync : null;
  return (
    <div style={{ display: 'flex', flexWrap: 'wrap', gap: space[8] }}>
      <Chip label={t.key_label}>
        {e.key(a.key_camelot ?? '?', b.key_camelot ?? '?', synced, e.keyVerdict[t.key_label])}
      </Chip>
      <Chip label={t.tempo_label}>
        {e.tempo(formatBpm(a.bpm ?? 0), formatBpm(b.bpm ?? 0), change)}
      </Chip>
      {a.energy !== null && b.energy !== null && (
        <Chip label={t.energy_label}>
          {e.energy(
            a.energy,
            b.energy,
            e.trend[b.energy > a.energy ? 'up' : b.energy < a.energy ? 'down' : 'same'],
          )}
        </Chip>
      )}
    </div>
  );
}

const card: CSSProperties = {
  borderRadius: radius.section,
  background: color.surface,
  border: `1px solid ${color.border}`,
  padding: space[20],
  display: 'flex',
  flexDirection: 'column',
  gap: space[14],
};

const h2: CSSProperties = { margin: 0, fontSize: 15, fontWeight: 600 };

function Chevron({ left = false }: { left?: boolean }) {
  return (
    <svg
      width="14"
      height="14"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      style={{ display: 'block', margin: '0 auto' }}
    >
      <path d={left ? 'M15 6l-6 6 6 6' : 'M9 6l6 6-6 6'} />
    </svg>
  );
}

function PointControl({
  label,
  seconds,
  auto,
  barSeconds,
  onChange,
}: {
  label: string;
  seconds: number;
  auto: boolean;
  barSeconds: number;
  onChange: (seconds: number) => void;
}) {
  const e = ro.transitionEditor;
  const step = PHRASE_BARS * barSeconds;
  const nudge: CSSProperties = {
    width: size.touch,
    height: size.touch,
    borderRadius: radius.buttonSm,
    border: `1px solid ${color.borderStrong}`,
    background: color.surface2,
    color: color.text,
    font: 'inherit',
    cursor: 'pointer',
  };
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: space[8] }}>
      <span style={{ flex: 1, color: color.textSoft }}>
        {label}:{' '}
        <strong style={{ color: color.text, fontVariantNumeric: 'tabular-nums' }}>
          {formatDuration(seconds)}
        </strong>
        {auto && <span style={{ color: color.textMuted }}> · {e.automatic}</span>}
      </span>
      <button
        type="button"
        aria-label={e.earlier(label)}
        onClick={() => onChange(Math.max(0, seconds - step))}
        style={nudge}
      >
        <Chevron left />
      </button>
      <button
        type="button"
        aria-label={e.later(label)}
        onClick={() => onChange(seconds + step)}
        style={nudge}
      >
        <Chevron />
      </button>
    </div>
  );
}

export function TransitionScreen() {
  const params = useParams();
  const mixId = Number(params.mixId);
  const position = Number(params.position);
  const transition = useTransition(mixId, position);
  const update = useUpdateTransition(mixId, position);
  const e = ro.transitionEditor;
  const previewKey = `${mixId}/${position}`;
  const preview = usePreview((s) => (s.key === previewKey ? s : null));

  // Ieșirea din ecran sau un plan nou opresc previzualizarea (s-ar auzi un plan vechi).
  const planVersion = JSON.stringify(transition.data?.plan ?? null);
  useEffect(() => () => transitionPreview.stop(), [planVersion]);

  if (transition.isError) {
    return (
      <div style={{ padding: space[28], display: 'flex', flexDirection: 'column', gap: space[12] }}>
        <p style={{ margin: 0, color: color.textMuted }}>{transition.error.message}</p>
        <Link to={`/mixuri/${mixId}`} style={{ color: color.accent }}>
          {ro.builder.back}
        </Link>
      </div>
    );
  }
  const t = transition.data;
  if (!t) return null;
  const plan = t.plan;
  const barA = 240 / (t.from_track.bpm ?? 120);
  const barB = 240 / (t.to_track.bpm ?? 120);

  return (
    <div
      style={{
        flex: 1,
        width: '100%',
        maxWidth: 1200,
        margin: '0 auto',
        padding: `${space[32]}px ${space[28]}px`,
        display: 'flex',
        flexDirection: 'column',
        gap: space[24],
      }}
    >
      <Link to={`/mixuri/${mixId}`} style={{ color: color.textMuted, fontSize: fontSize.meta }}>
        ← {e.back(t.mix_name)}
      </Link>

      <div
        style={{
          display: 'flex',
          flexWrap: 'wrap',
          alignItems: 'flex-end',
          justifyContent: 'space-between',
          gap: space[16],
        }}
      >
        <div>
          <span style={{ color: color.textMuted, fontSize: fontSize.meta }}>
            {e.heading(position, position + 1)}
          </span>
          <h1
            style={{
              margin: `${space[4]}px 0 0`,
              fontFamily: font.display,
              fontSize: fontSize.h1,
              fontWeight: 600,
              letterSpacing: '-0.02em',
            }}
          >
            {t.from_track.title} → {t.to_track.title}
          </h1>
        </div>
        <Chips t={t} />
      </div>

      <TransitionView transition={t} playheadT={preview?.t ?? null} />

      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
          gap: space[20],
        }}
      >
        <section style={card}>
          <h2 style={h2}>{e.length}</h2>
          <div role="group" aria-label={e.lengthGroup} style={{ display: 'flex', gap: space[6] }}>
            {LENGTHS.map((bars) => {
              const active = plan.length_bars === bars;
              return (
                <button
                  key={bars}
                  type="button"
                  aria-pressed={active}
                  onClick={() => update.mutate({ length_bars: bars })}
                  style={{
                    flex: 1,
                    height: size.touch,
                    borderRadius: radius.buttonSm,
                    border: active ? 0 : `1px solid ${color.borderStrong}`,
                    background: active ? color.accent : color.surface2,
                    color: active ? color.accentText : color.textSoft,
                    font: 'inherit',
                    fontWeight: active ? 600 : 400,
                    cursor: 'pointer',
                  }}
                >
                  {bars}
                </button>
              );
            })}
          </div>
          <p
            style={{ margin: 0, color: color.textMuted, fontSize: fontSize.meta, lineHeight: 1.5 }}
          >
            {e.lengthNote}
          </p>
          <h2 style={{ ...h2, marginTop: space[8] }}>{e.points}</h2>
          <PointControl
            label={e.aOut}
            seconds={plan.a_out_s}
            auto={plan.a_out_auto}
            barSeconds={barA}
            onChange={(s) => update.mutate({ a_out_s: s })}
          />
          <PointControl
            label={e.bIn}
            seconds={plan.b_in_s}
            auto={plan.b_in_auto}
            barSeconds={barB}
            onChange={(s) => update.mutate({ b_in_s: s })}
          />
          {!(plan.a_out_auto && plan.b_in_auto) && (
            <Button
              onClick={() => update.mutate({ reset_points: true })}
              style={{ alignSelf: 'flex-start' }}
            >
              {e.resetPoints}
            </Button>
          )}
        </section>

        <section style={{ ...card, gap: space[10] }}>
          <h2 style={{ ...h2, marginBottom: space[4] }}>{e.style}</h2>
          {STYLES.map((style) => {
            const on = plan.style === style;
            return (
              <label
                key={style}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: space[12],
                  padding: `${space[12]}px ${space[14]}px`,
                  borderRadius: radius.control,
                  cursor: 'pointer',
                  background: on ? color.accentSoftBg : color.surface2,
                  border: `1px solid ${on ? color.accent : color.border}`,
                }}
              >
                <input
                  type="radio"
                  name="stil"
                  value={style}
                  checked={on}
                  onChange={() => update.mutate({ style })}
                  style={{ width: 18, height: 18, accentColor: color.accent, margin: 0 }}
                />
                <span style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                  <span style={{ fontWeight: 500 }}>{e.styles[style].name}</span>
                  <span style={{ color: color.textMuted, fontSize: fontSize.meta }}>
                    {e.styles[style].hint}
                  </span>
                </span>
              </label>
            );
          })}
        </section>
      </div>

      <div style={{ display: 'flex', flexWrap: 'wrap', gap: space[10] }}>
        <Button
          variant="primary"
          style={{ height: 48, padding: `0 ${space[22]}px` }}
          disabled={preview?.status === 'loading'}
          onClick={() =>
            preview?.status === 'playing'
              ? transitionPreview.stop()
              : void transitionPreview.play(previewKey, plan, (deck, range) =>
                  fetchClip(deck === 'a' ? t.from_track.id : t.to_track.id, range.fromS, range.toS),
                )
          }
        >
          <svg width="14" height="14" viewBox="0 0 12 12" aria-hidden="true">
            {preview?.status === 'playing' ? (
              <path d="M2 2h8v8H2z" fill="currentColor" />
            ) : (
              <path d="M3 1.5v9l7.5-4.5z" fill="currentColor" />
            )}
          </svg>
          {preview?.status === 'loading'
            ? e.loading
            : preview?.status === 'playing'
              ? e.stop
              : e.listen}
        </Button>
        <Button
          onClick={() => update.mutate({ auto: true })}
          disabled={update.isPending}
          style={{ height: 48 }}
        >
          {e.auto}
        </Button>
      </div>
    </div>
  );
}
