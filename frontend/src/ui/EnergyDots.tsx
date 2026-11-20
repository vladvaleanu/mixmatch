import { ro } from '../i18n/ro';
import { color, radius } from '../theme/tokens';

const LEVELS = [1, 2, 3, 4, 5] as const;
const DOT = 8;

type Props = {
  value: number;
  manual: boolean;
  /** Fără `onChange`, punctele doar afișează. Cu el: click = corectare; click pe valoarea
   *  manuală curentă = revino la automat (null). */
  onChange?: (value: number | null) => void;
};

function Dot({ filled }: { filled: boolean }) {
  return (
    <span
      aria-hidden="true"
      style={{
        display: 'block',
        width: DOT,
        height: DOT,
        borderRadius: radius.round,
        background: filled ? color.accent : color.borderDashed,
      }}
    />
  );
}

export function EnergyDots({ value, manual, onChange }: Props) {
  const label = ro.energy.label(value, manual);
  if (!onChange) {
    return (
      <span role="img" aria-label={label} style={{ display: 'flex', gap: 4 }}>
        {LEVELS.map((level) => (
          <Dot key={level} filled={level <= value} />
        ))}
      </span>
    );
  }
  return (
    <span role="radiogroup" aria-label={label} title={label} style={{ display: 'flex' }}>
      {LEVELS.map((level) => (
        <button
          key={level}
          type="button"
          role="radio"
          aria-checked={level === value}
          aria-label={ro.energy.set(level)}
          onClick={(event) => {
            event.stopPropagation(); // în tabel, corectura nu selectează și rândul
            onChange(manual && level === value ? null : level);
          }}
          style={{
            // Ținta de click e mai mare decât punctul.
            padding: `10px 2px`,
            border: 0,
            background: 'transparent',
            cursor: 'pointer',
          }}
        >
          <Dot filled={level <= value} />
        </button>
      ))}
    </span>
  );
}
