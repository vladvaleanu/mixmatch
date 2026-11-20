import { ro } from '../i18n/ro';
import { color, fontSize, keyColor, radius, space } from '../theme/tokens';

type Props = { code: string; name: string | null };

/** Codul Camelot pe culoarea tonului; numele clasic apare la hover și pentru cititoarele de ecran. */
export function KeyPill({ code, name }: Props) {
  return (
    <span
      title={name ?? undefined}
      aria-label={ro.key.label(code, name)}
      style={{
        display: 'inline-block',
        minWidth: 36,
        padding: `${space[4]}px ${space[8]}px`,
        borderRadius: radius.pill,
        background: keyColor(code),
        color: color.accentText,
        fontSize: fontSize.meta,
        fontWeight: 600,
        textAlign: 'center',
        fontVariantNumeric: 'tabular-nums',
      }}
    >
      {code}
    </span>
  );
}
