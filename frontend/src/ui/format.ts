/** 124 → „124”; 123.5 → „123,5”. */
export function formatBpm(bpm: number): string {
  return Number.isInteger(bpm) ? String(bpm) : bpm.toFixed(1).replace('.', ',');
}

/** 2580 → „43 min”; 4500 → „1 h 15 min”. */
export function formatMinutes(seconds: number): string {
  const minutes = Math.round(seconds / 60);
  const h = Math.floor(minutes / 60);
  return h > 0 ? `${h} h ${minutes % 60} min` : `${minutes} min`;
}

/** 312.4 → „5:12”; 3725 → „1:02:05”. */
export function formatDuration(seconds: number): string {
  const total = Math.max(0, Math.round(seconds));
  const h = Math.floor(total / 3600);
  const m = Math.floor((total % 3600) / 60);
  const s = String(total % 60).padStart(2, '0');
  return h > 0 ? `${h}:${String(m).padStart(2, '0')}:${s}` : `${m}:${s}`;
}
