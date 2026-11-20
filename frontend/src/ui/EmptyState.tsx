import type { ReactNode } from 'react';

import { color, font, fontSize, radius, space } from '../theme/tokens';

type Props = { title: string; text: string; action?: ReactNode };

/** Starea goală a unui ecran: ce lipsește și ce poți face. */
export function EmptyState({ title, text, action }: Props) {
  return (
    <div
      style={{
        padding: `${space[32]}px ${space[28]}px`,
        borderRadius: radius.section,
        border: `1.5px dashed ${color.borderDashed}`,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'flex-start',
        gap: space[12],
        maxWidth: 560,
      }}
    >
      <svg width="28" height="28" viewBox="0 0 28 28" aria-hidden="true">
        <circle cx="14" cy="14" r="12" fill="none" stroke={color.accent} strokeWidth="2" />
        <circle cx="14" cy="14" r="3" fill={color.accent} />
      </svg>
      <h2 style={{ margin: 0, fontFamily: font.display, fontSize: fontSize.logo, fontWeight: 600 }}>
        {title}
      </h2>
      <p style={{ margin: 0, color: color.textSoft, lineHeight: 1.6 }}>{text}</p>
      {action}
    </div>
  );
}
