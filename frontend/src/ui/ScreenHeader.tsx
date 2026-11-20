import { color, font, fontSize, space } from '../theme/tokens';

type Props = { title: string; subtitle: string };

export function ScreenHeader({ title, subtitle }: Props) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: space[6] }}>
      <h1
        style={{
          margin: 0,
          fontFamily: font.display,
          fontSize: fontSize.h1,
          fontWeight: 600,
          letterSpacing: '-0.02em',
        }}
      >
        {title}
      </h1>
      <p style={{ margin: 0, color: color.textMuted }}>{subtitle}</p>
    </div>
  );
}
