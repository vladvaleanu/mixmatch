import { color, radius, space } from '../theme/tokens';

type Props<T extends string> = {
  label: string;
  options: { value: T; label: string }[];
  value: T;
  onChange: (value: T) => void;
};

/** Grup de butoane cu `aria-pressed` (forma setului, lungimea tranziției). */
export function Segmented<T extends string>({ label, options, value, onChange }: Props<T>) {
  return (
    <div
      role="group"
      aria-label={label}
      style={{
        display: 'flex',
        gap: space[4],
        padding: space[4],
        borderRadius: radius.control,
        background: color.surface2,
      }}
    >
      {options.map((option) => {
        const active = option.value === value;
        return (
          <button
            key={option.value}
            type="button"
            aria-pressed={active}
            onClick={() => onChange(option.value)}
            style={{
              height: 36,
              padding: `0 ${space[14]}px`,
              borderRadius: radius.buttonSm,
              border: 0,
              background: active ? color.surface3 : 'transparent',
              color: active ? color.text : color.textSoft,
              font: 'inherit',
              fontWeight: active ? 500 : 400,
              cursor: 'pointer',
            }}
          >
            {option.label}
          </button>
        );
      })}
    </div>
  );
}
