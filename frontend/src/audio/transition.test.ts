import { describe, expect, it } from 'vitest';

import { FakeContext } from './fakeAudio';
import { clipRanges, valueAt, type Plan } from './plan';
import { scheduleTransition } from './transition';

const L = 30;

function plan(overrides: Partial<Plan> = {}): Plan {
  return {
    style: 'eq_swap',
    length_bars: 16,
    length_s: L,
    a_out_s: 300,
    b_in_s: 0.5,
    a_start_s: 300,
    b_start_s: 0.5,
    speed_b: 0.98,
    gain_a_db: -6,
    gain_b_db: 0,
    bass_shelf_hz: 150,
    echo_taps: [
      { delay_s: 0.36, gain: 1 },
      { delay_s: 0.72, gain: 0.45 },
    ],
    preview_start_s: -8,
    preview_end_s: L + 8,
    a_out_auto: true,
    b_in_auto: true,
    automations: [
      {
        target: 'a_volume',
        points: [
          { t_s: 0, value: 1 },
          { t_s: 15, value: 1 },
          { t_s: 30, value: 0 },
        ],
      },
      {
        target: 'b_volume',
        points: [
          { t_s: 0, value: 0 },
          { t_s: 15, value: 1 },
          { t_s: 30, value: 1 },
        ],
      },
      {
        target: 'a_bass',
        points: [
          { t_s: 0, value: 0 },
          { t_s: 15, value: 0 },
          { t_s: 15, value: -26 },
          { t_s: 30, value: -26 },
        ],
      },
      {
        target: 'b_bass',
        points: [
          { t_s: 0, value: -26 },
          { t_s: 15, value: -26 },
          { t_s: 15, value: 0 },
          { t_s: 30, value: 0 },
        ],
      },
    ],
    ...overrides,
  };
}

const clips = { a: {} as AudioBuffer, b: {} as AudioBuffer };

function run(p: Plan) {
  const ctx = new FakeContext();
  scheduleTransition(
    ctx as unknown as BaseAudioContext,
    p,
    clips,
    ctx.destination as unknown as AudioNode,
    10,
  );
  return ctx;
}

describe('valueAt', () => {
  const points = [
    { t_s: 0, value: 0 },
    { t_s: 10, value: 1 },
    { t_s: 10, value: 0.5 },
  ];
  it.each([
    [-5, 0],
    [5, 0.5],
    [10, 1],
    [20, 0.5],
  ])('t = %s → %s', (t, v) => expect(valueAt(points, t)).toBeCloseTo(v));
});

describe('clipRanges', () => {
  it('ia din A și din B exact fereastra', () => {
    const r = clipRanges(plan());
    expect(r.a).toEqual({ fromS: 292, toS: 338, atS: 0 });
    // La t = 0 B e la 0,5 s în fișier, deci fișierul ei începe cu 0,5 / 0,98 s mai devreme.
    expect(r.b.atS).toBeCloseTo(8 - 0.5 / 0.98);
    expect(r.b.fromS).toBeCloseTo(0);
    expect(r.b.toS).toBeCloseTo(0.5 + 38 * 0.98);
  });

  it('o piesă care începe după fereastră: A la începutul fișierului, B mai târziu', () => {
    const r = clipRanges(plan({ a_start_s: 3, b_start_s: -14.7 })); // B tace până la t = 15
    expect(r.a).toEqual({ fromS: 0, toS: 41, atS: 5 });
    expect(r.b.fromS).toBeCloseTo(0);
    expect(r.b.atS).toBeCloseTo(8 + 15);
  });
});

describe('scheduleTransition', () => {
  it('pornește A și B la momentele din plan, B la viteza din plan', () => {
    const ctx = run(plan());
    const [a, b] = ctx.sources;
    expect(a?.start).toHaveBeenCalledWith(10);
    expect(b?.start).toHaveBeenCalledWith(10 + 8 - 0.5 / 0.98);
    expect(a?.playbackRate.value).toBe(1);
    expect(b?.playbackRate.value).toBe(0.98);
  });

  it('volumul lui A urmează planul, cu auto-gain-ul aplicat', () => {
    const ctx = run(plan());
    const g = 10 ** (-6 / 20);
    const volumeA = ctx.gains[0]?.gain.events ?? [];
    expect(volumeA[0]).toEqual(['set', g, 10]); // la începutul ferestrei (t = −8)
    expect(volumeA.slice(1).map(([k, v, t]) => [k, +v.toFixed(4), t])).toEqual([
      ['ramp', +g.toFixed(4), 18],
      ['ramp', +g.toFixed(4), 33],
      ['ramp', 0, 48],
    ]);
  });

  it('schimbul de bas e un salt pe filtrul low-shelf', () => {
    const ctx = run(plan());
    const shelfA = ctx.filters[0];
    expect(shelfA?.type).toBe('lowshelf');
    expect(shelfA?.frequency.value).toBe(150);
    expect(shelfA?.gain.events).toEqual([
      ['set', 0, 10],
      ['ramp', 0, 18],
      ['ramp', 0, 33],
      ['set', -26, 33],
      ['ramp', -26, 48],
    ]);
  });

  it('ecoul: copii întârziate ale lui A, deschise de automatizare', () => {
    const p = plan({
      style: 'echo_out',
      automations: [
        ...plan().automations.filter((a) => a.target.endsWith('volume')),
        {
          target: 'a_echo',
          points: [
            { t_s: 0, value: 0 },
            { t_s: 15, value: 0.6 },
            { t_s: 15, value: 0 },
          ],
        },
      ],
    });
    const ctx = run(p);
    expect(ctx.delays.map((d) => d.delayTime.value)).toEqual([0.36, 0.72]);
    const send = ctx.gains.find((g) => g.outputs.some((o) => o.kind === 'delay'));
    expect(send?.outputs).toHaveLength(2); // câte o întârziere pe repetare
    expect(send?.gain.events.at(-1)).toEqual(['set', 0, 33]); // la tăietură intrarea se închide
  });

  it('fără ecou în plan, nu există întârzieri', () => {
    expect(run(plan()).delays).toHaveLength(0);
  });
});
