// Un AudioContext fals pentru teste: înregistrează ce se programează, nu redă nimic.
import { vi } from 'vitest';

export type ParamEvent = [kind: 'set' | 'ramp', value: number, time: number];

export class FakeParam {
  value = 0;
  events: ParamEvent[] = [];
  setValueAtTime(value: number, time: number) {
    this.events.push(['set', value, time]);
    return this;
  }
  linearRampToValueAtTime(value: number, time: number) {
    this.events.push(['ramp', value, time]);
    return this;
  }
}

export class FakeNode {
  kind: string;
  outputs: FakeNode[] = [];
  constructor(kind: string) {
    this.kind = kind;
  }
  connect<T extends FakeNode>(node: T): T {
    this.outputs.push(node);
    return node;
  }
}

export class FakeSource extends FakeNode {
  buffer: unknown = null;
  playbackRate = new FakeParam();
  start = vi.fn();
  stop = vi.fn();
  constructor() {
    super('source');
  }
}

export class FakeContext {
  currentTime = 0;
  destination = new FakeNode('destination');
  sources: FakeSource[] = [];
  gains: (FakeNode & { gain: FakeParam })[] = [];
  filters: (FakeNode & { type: string; frequency: FakeParam; gain: FakeParam })[] = [];
  delays: (FakeNode & { delayTime: FakeParam })[] = [];
  resume = vi.fn(async () => undefined);
  decodeAudioData = vi.fn(async (data: ArrayBuffer) => ({ length: data.byteLength }));

  createBufferSource() {
    const s = new FakeSource();
    this.sources.push(s);
    return s;
  }
  createGain() {
    const g = Object.assign(new FakeNode('gain'), { gain: new FakeParam() });
    this.gains.push(g);
    return g;
  }
  createBiquadFilter() {
    const f = Object.assign(new FakeNode('filter'), {
      type: '',
      frequency: new FakeParam(),
      gain: new FakeParam(),
    });
    this.filters.push(f);
    return f;
  }
  createDelay() {
    const d = Object.assign(new FakeNode('delay'), { delayTime: new FakeParam() });
    this.delays.push(d);
    return d;
  }
  createMediaElementSource() {
    return new FakeNode('media');
  }
}
