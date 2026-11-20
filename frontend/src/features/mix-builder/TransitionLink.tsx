import { Link } from 'react-router-dom';

import type { Schemas } from '../../api/client';
import { ro } from '../../i18n/ro';
import { color, fontSize, radius, space } from '../../theme/tokens';

type Transition = Schemas['ReportTransitionOut'];

const look = {
  smooth: {
    bg: color.accentSoftBg,
    fg: color.accentSoftText,
    mark: color.accent,
    r: radius.round,
    rotate: 0,
  },
  good: { bg: color.infoSoftBg, fg: color.infoSoftText, mark: color.info, r: 3, rotate: 0 },
  caution: { bg: color.warnSoftBg, fg: color.warnSoftText, mark: color.warn, r: 2, rotate: 45 },
} as const;

export const TRANSITION_WIDTH = 76;

/** Eticheta dintre două carduri: formă + culoare + text; motivul la hover și pentru cititoare.
 *  Click deschide editorul tranziției. */
export function TransitionLink({
  transition,
  fromTitle,
  toTitle,
  to,
}: {
  transition: Transition | undefined;
  fromTitle: string;
  toTitle: string;
  /** Adresa editorului acestei tranziții. */
  to: string;
}) {
  const box = {
    width: TRANSITION_WIDTH,
    flex: 'none',
    margin: `0 ${space[6]}px`,
    borderRadius: radius.control,
  } as const;
  if (!transition) return <span aria-hidden="true" style={box} />; // în timpul unui drag
  if (!transition.label) {
    return (
      <span
        title={ro.report.notAnalyzed}
        style={{
          ...box,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: color.textMuted,
        }}
      >
        ?
      </span>
    );
  }
  const l = look[transition.label];
  const text = ro.transition[transition.label];
  return (
    <Link
      to={to}
      title={transition.reason ?? undefined}
      aria-label={ro.report.transition(fromTitle, toTitle, text, transition.reason ?? '')}
      style={{
        ...box,
        background: l.bg,
        color: l.fg,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        gap: space[8],
        textDecoration: 'none',
      }}
    >
      <span
        aria-hidden="true"
        style={{
          width: 10,
          height: 10,
          borderRadius: l.r,
          transform: `rotate(${l.rotate}deg)`,
          background: l.mark,
        }}
      />
      <span style={{ fontSize: fontSize.label, fontWeight: 600 }}>{text}</span>
    </Link>
  );
}
