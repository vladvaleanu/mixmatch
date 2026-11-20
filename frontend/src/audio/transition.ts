// Execută planul unei tranziții în Web Audio. Ce se aude vine exclusiv din plan și din bucățile
// de audio decupate de backend. Merge pe orice BaseAudioContext (și Offline, pentru teste).
import { clipRanges, valueAt, type Automation, type Plan } from './plan';

type Target = Automation['target'];

const dbToGain = (db: number) => 10 ** (db / 20);

/** Programează o automatizare pe un parametru; `map` transformă valoarea din plan. */
function automate(
  param: AudioParam,
  plan: Plan,
  auto: Automation | undefined,
  fallback: number,
  map: (v: number) => number,
  windowToCtx: (t: number) => number,
) {
  const ws = plan.preview_start_s;
  if (!auto) {
    param.setValueAtTime(map(fallback), windowToCtx(ws));
    return;
  }
  param.setValueAtTime(map(valueAt(auto.points, ws)), windowToCtx(ws));
  let previous: number | null = null;
  for (const point of auto.points) {
    if (point.t_s > ws) {
      const at = windowToCtx(point.t_s);
      if (previous === point.t_s) param.setValueAtTime(map(point.value), at);
      else param.linearRampToValueAtTime(map(point.value), at);
    }
    previous = point.t_s;
  }
}

export type Clips = { a: AudioBuffer; b: AudioBuffer };

/**
 * Construiește graful și programează totul de la `startAt` (timpul contextului).
 * deck: sursă → low-shelf (bas) → volum → ieșire; A trimite după filtru și în ecou
 * (copii întârziate), care merge direct la ieșire. Întoarce o funcție de oprire.
 */
export function scheduleTransition(
  ctx: BaseAudioContext,
  plan: Plan,
  clips: Clips,
  output: AudioNode,
  startAt: number,
): () => void {
  const ranges = clipRanges(plan);
  const byTarget = new Map<Target, Automation>(plan.automations.map((a) => [a.target, a]));
  const windowToCtx = (t: number) => startAt + (t - plan.preview_start_s);
  const sources: AudioBufferSourceNode[] = [];

  const deck = (
    name: 'a' | 'b',
    buffer: AudioBuffer,
    atS: number,
    speed: number,
    gainDb: number,
  ) => {
    const source = ctx.createBufferSource();
    source.buffer = buffer;
    source.playbackRate.value = speed; // stil vinil: viteza și tonul se schimbă împreună
    const shelf = ctx.createBiquadFilter();
    shelf.type = 'lowshelf';
    shelf.frequency.value = plan.bass_shelf_hz;
    const volume = ctx.createGain();
    source.connect(shelf).connect(volume).connect(output);
    const auto = (target: Target) => byTarget.get(target);
    const level = dbToGain(gainDb);
    automate(
      volume.gain,
      plan,
      auto(`${name}_volume`),
      name === 'a' ? 1 : 0,
      (v) => v * level,
      windowToCtx,
    );
    automate(shelf.gain, plan, auto(`${name}_bass`), 0, (v) => v, windowToCtx);
    source.start(startAt + atS);
    sources.push(source);
    return { shelf, level };
  };

  const a = deck('a', clips.a, ranges.a.atS, 1, plan.gain_a_db);
  deck('b', clips.b, ranges.b.atS, plan.speed_b, plan.gain_b_db);

  const echo = byTarget.get('a_echo');
  if (echo) {
    const send = ctx.createGain();
    a.shelf.connect(send);
    automate(send.gain, plan, echo, 0, (v) => v * a.level, windowToCtx);
    for (const tap of plan.echo_taps) {
      const delay = ctx.createDelay(Math.max(1, tap.delay_s + 0.1));
      delay.delayTime.value = tap.delay_s;
      const gain = ctx.createGain();
      gain.gain.value = tap.gain;
      send.connect(delay).connect(gain).connect(output);
    }
  }

  return () => {
    for (const source of sources) {
      try {
        source.stop();
      } catch {
        /* deja oprită */
      }
    }
  };
}

/** Durata ferestrei de previzualizare, în secunde. */
export function previewLength(plan: Plan): number {
  return plan.preview_end_s - plan.preview_start_s;
}
