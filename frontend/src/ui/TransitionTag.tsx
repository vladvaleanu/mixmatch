import type { Schemas } from '../api/client';
import { ro } from '../i18n/ro';
import { color, fontSize, radius, space } from '../theme/tokens';

type Label = Schemas['MatchOut']['label'];

// Fiecare etichetă are formă proprie, nu doar culoare (design.md).
const styles: Record<
  Label,
  { bg: string; fg: string; mark: string; shape: 'circle' | 'square' | 'diamond' }
> = {
  smooth: { bg: color.accentSoftBg, fg: color.accentSoftText, mark: color.accent, shape: 'circle' },
  good: { bg: color.infoSoftBg, fg: color.infoSoftText, mark: color.info, shape: 'square' },
  caution: { bg: color.warnSoftBg, fg: color.warnSoftText, mark: color.warn, shape: 'diamond' },
};

export function TransitionTag({ label }: { label: Label }) {
  const s = styles[label];
  return (
    <span
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: space[6],
        padding: `${space[4]}px ${space[10]}px`,
        borderRadius: radius.round,
        background: s.bg,
        color: s.fg,
        fontSize: fontSize.meta,
        fontWeight: 500,
        whiteSpace: 'nowrap',
      }}
    >
      <svg width="8" height="8" viewBox="0 0 8 8" aria-hidden="true">
        {s.shape === 'circle' && <circle cx="4" cy="4" r="4" fill={s.mark} />}
        {s.shape === 'square' && <rect width="8" height="8" rx="1" fill={s.mark} />}
        {s.shape === 'diamond' && <path d="M4 0L8 4L4 8L0 4Z" fill={s.mark} />}
      </svg>
      {ro.transition[label]}
    </span>
  );
}
