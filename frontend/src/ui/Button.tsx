import type { ButtonHTMLAttributes, CSSProperties } from 'react';

import { color, radius, size, space } from '../theme/tokens';

type Variant = 'primary' | 'secondary';

const variants: Record<Variant, CSSProperties> = {
  primary: { background: color.accent, color: color.accentText, border: 0, fontWeight: 600 },
  secondary: {
    background: color.surface2,
    color: color.text,
    border: `1px solid ${color.borderStrong}`,
    fontWeight: 500,
  },
};

type Props = ButtonHTMLAttributes<HTMLButtonElement> & { variant?: Variant };

export function Button({ variant = 'secondary', style, type = 'button', ...rest }: Props) {
  return (
    <button
      type={type}
      style={{
        height: size.touch,
        padding: `0 ${space[18]}px`,
        borderRadius: radius.control,
        font: 'inherit',
        display: 'inline-flex',
        alignItems: 'center',
        justifyContent: 'center',
        gap: space[8],
        cursor: rest.disabled ? 'default' : 'pointer',
        opacity: rest.disabled ? 0.6 : 1,
        ...variants[variant],
        ...style,
      }}
      {...rest}
    />
  );
}
