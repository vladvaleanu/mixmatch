import type { Schemas } from '../../api/client';
import { ro } from '../../i18n/ro';
import { color, radius } from '../../theme/tokens';

type Report = Schemas['ReportOut'];

const W = 1000;
const H = 150;
const PAD_X = 40;
const TOP = 22; // energia 5
const BOTTOM = 128; // energia 1

const y = (energy: number) => BOTTOM - ((energy - 1) / 4) * (BOTTOM - TOP);

/** Graficul din machetă: forma dorită punctată (gri), mixul cu linie plină (accent).
 *  Punctul unei piese în care se intră printr-o tranziție „Atenție” e în `warn`. */
export function EnergyCurve({ report }: { report: Report }) {
  const n = report.energy.length;
  const x = (i: number) => (n <= 1 ? W / 2 : PAD_X + (i * (W - 2 * PAD_X)) / (n - 1));
  const caution = new Set(
    report.transitions.filter((t) => t.label === 'caution').map((t) => t.position),
  );
  const targets = report.energy.map((p, i) =>
    p.target === null ? null : `${x(i)},${y(p.target)}`,
  );
  const actual = report.energy
    .map((p, i) => (p.actual === null ? null : { i, x: x(i), y: y(p.actual) }))
    .filter((p) => p !== null);
  const values = report.energy.map((p) => p.actual ?? '?').join(', ');

  return (
    <div style={{ position: 'relative' }}>
      <svg
        viewBox={`0 0 ${W} ${H}`}
        preserveAspectRatio="none"
        role="img"
        aria-label={ro.report.curveLabel(values)}
        style={{ width: '100%', height: H, display: 'block' }}
      >
        {[TOP + 8, (TOP + BOTTOM) / 2, BOTTOM - 8].map((lineY) => (
          <line
            key={lineY}
            x1="0"
            y1={lineY}
            x2={W}
            y2={lineY}
            stroke={color.border}
            strokeWidth="1"
          />
        ))}
        {targets.every((t) => t !== null) && n > 1 && (
          <polyline
            points={targets.join(' ')}
            fill="none"
            stroke={color.waveIdle}
            strokeWidth="2"
            strokeDasharray="6 6"
            vectorEffect="non-scaling-stroke"
          />
        )}
        {actual.length > 1 && (
          <polyline
            points={actual.map((p) => `${p.x},${p.y}`).join(' ')}
            fill="none"
            stroke={color.accent}
            strokeWidth="3"
            strokeLinejoin="round"
            vectorEffect="non-scaling-stroke"
          />
        )}
      </svg>
      {/* Punctele sunt HTML, ca să rămână rotunde când graficul se întinde pe lățime. */}
      {actual.map((p) => (
        <span
          key={p.i}
          aria-hidden="true"
          style={{
            position: 'absolute',
            left: `${(p.x / W) * 100}%`,
            top: p.y,
            width: 12,
            height: 12,
            marginLeft: -6,
            marginTop: -6,
            borderRadius: radius.round,
            background: caution.has(p.i) ? color.warn : color.accent,
          }}
        />
      ))}
    </div>
  );
}
