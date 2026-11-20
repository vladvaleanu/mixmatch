// Citirea planului unei tranziții (fără Web Audio): valori în timp și bucățile de audio necesare.
import type { Schemas } from '../api/client';

export type Plan = Schemas['PlanOut'];
export type Automation = Plan['automations'][number];
export type Point = Automation['points'][number];

/** Valoarea unei automatizări la momentul t: liniar între puncte; înainte/după = capetele. */
export function valueAt(points: Point[], t: number): number {
  let previous: Point | undefined;
  for (const point of points) {
    if (t <= point.t_s) {
      if (!previous || point.t_s === previous.t_s) return point.value;
      const k = (t - previous.t_s) / (point.t_s - previous.t_s);
      return previous.value + (point.value - previous.value) * k;
    }
    previous = point;
  }
  return previous?.value ?? 0;
}

/** O bucată de fișier de redat: [fromS, toS] din piesă, pornită la `atS` în fereastră. */
export type ClipRange = { fromS: number; toS: number; atS: number };

/** Bucățile din A și din B pentru fereastra de previzualizare (timpii ferestrei de la 0). */
export function clipRanges(plan: Plan): { a: ClipRange; b: ClipRange } {
  const ws = plan.preview_start_s;
  const we = plan.preview_end_s;
  const aFrom = plan.a_start_s + ws;
  // B începe când poziția ei în fișier ajunge la 0 (b_start_s poate fi negativ).
  const bStartT = Math.max(ws, -plan.b_start_s / plan.speed_b);
  return {
    a: { fromS: Math.max(0, aFrom), toS: plan.a_start_s + we, atS: Math.max(0, -aFrom) },
    b: {
      // Max cu 0: rotunjirile pot da un −0,000…, pe care serverul îl refuză.
      fromS: Math.max(0, plan.b_start_s + bStartT * plan.speed_b),
      toS: plan.b_start_s + we * plan.speed_b,
      atS: bStartT - ws,
    },
  };
}
