import type { KeyboardEvent, MouseEvent } from 'react';

import { ro } from '../i18n/ro';
import { color } from '../theme/tokens';

type Props = {
  peaks: number[]; // 0–255
  height: number;
  /** Câte bare să desenez; vârfurile se grupează (maximul pe grup). Implicit: câte vârfuri sunt. */
  bars?: number;
  selected?: boolean;
  /** 0–1: partea deja ascultată se colorează în accent. */
  progress?: number;
  /** Click (sau săgeți) pe formă = derulare; primește poziția 0–1. */
  onSeek?: (fraction: number) => void;
};

const BAR = 2;
const GAP = 2;
const MIN_BAR = 2;
const KEY_STEP = 0.02;

function group(peaks: number[], bars: number): number[] {
  if (bars >= peaks.length) return peaks;
  return Array.from({ length: bars }, (_, i) => {
    const from = Math.floor((i * peaks.length) / bars);
    const to = Math.max(from + 1, Math.floor(((i + 1) * peaks.length) / bars));
    return Math.max(...peaks.slice(from, to));
  });
}

/** Bare de 2 px cu spațiu de 2 px; înălțimea vine din vârfuri (design.md). */
export function Waveform({ peaks, height, bars, selected = false, progress, onSeek }: Props) {
  const shown = group(peaks, bars ?? peaks.length);
  const width = shown.length * (BAR + GAP) - GAP;
  const idle = selected ? color.accent : color.waveIdle;
  const playedBars = progress === undefined ? -1 : Math.round(progress * shown.length);

  const svg = (
    <svg width={width} height={height} aria-hidden="true" style={{ display: 'block' }}>
      {shown.map((peak, i) => {
        const h = Math.max(MIN_BAR, (peak / 255) * height);
        return (
          <rect
            key={i}
            x={i * (BAR + GAP)}
            y={(height - h) / 2}
            width={BAR}
            height={h}
            rx={1}
            fill={i < playedBars ? color.accent : idle}
          />
        );
      })}
    </svg>
  );
  if (!onSeek) return svg;

  const seekTo = (event: MouseEvent<HTMLDivElement>) => {
    const box = event.currentTarget.getBoundingClientRect();
    onSeek(Math.min(Math.max((event.clientX - box.left) / box.width, 0), 1));
  };
  const onKey = (event: KeyboardEvent<HTMLDivElement>) => {
    const delta = { ArrowRight: KEY_STEP, ArrowLeft: -KEY_STEP }[event.key];
    if (delta === undefined) return;
    event.preventDefault();
    onSeek(Math.min(Math.max((progress ?? 0) + delta, 0), 1));
  };
  return (
    <div
      role="slider"
      tabIndex={0}
      aria-label={ro.player.seek}
      aria-valuemin={0}
      aria-valuemax={100}
      aria-valuenow={Math.round((progress ?? 0) * 100)}
      onClick={seekTo}
      onKeyDown={onKey}
      style={{ cursor: 'pointer', width, maxWidth: '100%' }}
    >
      {svg}
    </div>
  );
}
