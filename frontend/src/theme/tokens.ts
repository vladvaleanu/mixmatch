// Singura sursă pentru culori, fonturi, spațieri și raze. Valorile vin 1:1 din docs/design.md.

export const color = {
  bg: '#111214',
  surface: '#16171A',
  surface2: '#1A1B1F',
  surface3: '#22242A',
  control: '#24262C',
  border: '#24252B',
  borderStrong: '#2A2C33',
  borderDashed: '#34363E',
  text: '#F2F2F0',
  textSoft: '#C9CAD0',
  textMuted: '#A4A6AE',
  waveIdle: '#6B6E78',
  accent: '#C6F36B',
  accentText: '#111214',
  accentSoftBg: '#1F2418',
  accentSoftBgStrong: '#2C3320',
  accentSoftText: '#E2FFA8',
  info: '#7FB2FF',
  infoSoftBg: '#1A2130',
  infoSoftText: '#CFE0FF',
  warn: '#F5B85B',
  warnSoftBg: '#2A2418',
  warnSoftText: '#FFE2A8',
  overlay: 'rgba(17, 18, 20, 0.72)',
} as const;

export const font = {
  text: 'Inter, system-ui, sans-serif',
  display: "'Space Grotesk', Inter, sans-serif",
} as const;

export const fontSize = {
  label: 12,
  meta: 13,
  base: 14,
  logo: 20,
  panelTitle: 24,
  h1: 32,
} as const;

export const space = {
  4: 4,
  6: 6,
  8: 8,
  10: 10,
  12: 12,
  14: 14,
  16: 16,
  18: 18,
  20: 20,
  22: 22,
  24: 24,
  28: 28,
  32: 32,
} as const;

export const radius = {
  pill: 8,
  buttonSm: 10,
  control: 12,
  card: 14,
  section: 16,
  round: 999,
} as const;

export const size = {
  touch: 44,
} as const;

export const zIndex = {
  dialog: 100,
  toast: 200,
} as const;

/** Nuanța tonului pe roata Camelot (din design.md): cifra n → (n·30 + 60) mod 360. */
function keyHue(camelot: string): number {
  return (Number.parseInt(camelot, 10) * 30 + 60) % 360;
}

/** Fundalul unui KeyPill. */
export function keyColor(camelot: string): string {
  return `hsl(${keyHue(camelot)}, 60%, 74%)`;
}

/** Coperta-placeholder a unei piese: aceeași nuanță, mai închisă. Fără ton: `control`. */
export function coverColor(camelot: string | null): string {
  return camelot ? `hsl(${keyHue(camelot)}, 35%, 32%)` : color.control;
}
