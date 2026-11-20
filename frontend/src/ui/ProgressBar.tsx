import { color, radius } from '../theme/tokens';

type Props = { value: number; label: string };

/** Bară de progres; `value` între 0 și 1. */
export function ProgressBar({ value, label }: Props) {
  const percent = Math.round(Math.min(Math.max(value, 0), 1) * 100);
  return (
    <div
      role="progressbar"
      aria-label={label}
      aria-valuemin={0}
      aria-valuemax={100}
      aria-valuenow={percent}
      style={{ height: 8, borderRadius: radius.round, background: color.surface3 }}
    >
      <div
        style={{
          width: `${percent}%`,
          height: '100%',
          borderRadius: radius.round,
          background: color.accent,
          transition: 'width 200ms',
        }}
      />
    </div>
  );
}
