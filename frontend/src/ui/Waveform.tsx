import { color } from '../theme/tokens';

type Props = {
  peaks: number[]; // 0–255
  height: number;
  selected?: boolean;
};

const BAR = 2;
const GAP = 2;
const MIN_BAR = 2;

/** Bare de 2 px cu spațiu de 2 px; înălțimea vine din vârfuri (design.md). */
export function Waveform({ peaks, height, selected = false }: Props) {
  const fill = selected ? color.accent : color.waveIdle;
  return (
    <svg
      width={peaks.length * (BAR + GAP) - GAP}
      height={height}
      aria-hidden="true"
      style={{ display: 'block' }}
    >
      {peaks.map((peak, i) => {
        const h = Math.max(MIN_BAR, (peak / 255) * height);
        return (
          <rect
            key={i}
            x={i * (BAR + GAP)}
            y={(height - h) / 2}
            width={BAR}
            height={h}
            rx={1}
            fill={fill}
          />
        );
      })}
    </svg>
  );
}
