import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { player, transitionPreview, usePlayer, usePreview } from './engine';
import { FakeContext } from './fakeAudio';
import type { Plan } from './plan';

const FakeAudioContext = FakeContext;

const created: HTMLMediaElement[] = [];

beforeEach(() => {
  vi.stubGlobal('AudioContext', FakeAudioContext);
  // jsdom nu redă audio: play/pause doar trimit evenimentele, ca un browser.
  vi.spyOn(HTMLMediaElement.prototype, 'play').mockImplementation(function (
    this: HTMLMediaElement,
  ) {
    if (!created.includes(this)) created.push(this);
    this.dispatchEvent(new Event('play'));
    return Promise.resolve();
  });
  vi.spyOn(HTMLMediaElement.prototype, 'pause').mockImplementation(function (
    this: HTMLMediaElement,
  ) {
    this.dispatchEvent(new Event('pause'));
  });
});

afterEach(() => {
  player.pause();
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
});

describe('player', () => {
  it('pornește și oprește aceeași piesă', () => {
    player.toggle(1, '/api/tracks/1/audio', 300);
    expect(usePlayer.getState()).toMatchObject({ trackId: 1, playing: true, durationS: 300 });

    player.toggle(1, '/api/tracks/1/audio', 300);
    expect(usePlayer.getState().playing).toBe(false);
  });

  it('o piesă nouă o înlocuiește pe cea care cântă, cu un singur element audio', () => {
    player.toggle(1, '/api/tracks/1/audio', 300);
    player.toggle(2, '/api/tracks/2/audio', 200);

    expect(usePlayer.getState()).toMatchObject({ trackId: 2, playing: true, positionS: 0 });
    expect(created).toHaveLength(1);
    expect(created[0]?.src).toContain('/api/tracks/2/audio');
  });

  it('derulează la poziția cerută și cântă de acolo', () => {
    player.playFrom(3, '/api/tracks/3/audio', 400, 120);
    expect(usePlayer.getState()).toMatchObject({ trackId: 3, playing: true, positionS: 120 });
    expect(created[0]?.currentTime).toBe(120);
  });
});

describe('previzualizarea tranziției', () => {
  const plan = {
    style: 'crossfade',
    length_s: 10,
    a_start_s: 50,
    b_start_s: 0,
    speed_b: 1,
    gain_a_db: 0,
    gain_b_db: 0,
    bass_shelf_hz: 150,
    echo_taps: [],
    preview_start_s: -2,
    preview_end_s: 12,
    automations: [],
  } as unknown as Plan;

  it('încarcă bucățile din plan, cântă, și oprește playerul', async () => {
    player.toggle(1, '/api/tracks/1/audio', 300);
    expect(usePlayer.getState().playing).toBe(true);

    const load = vi.fn(async () => new ArrayBuffer(8));
    await transitionPreview.play('7/3', plan, load);

    expect(load).toHaveBeenCalledWith('a', { fromS: 48, toS: 62, atS: 0 });
    expect(load).toHaveBeenCalledWith('b', { fromS: 0, toS: 12, atS: 2 });
    expect(usePreview.getState()).toMatchObject({ key: '7/3', status: 'playing' });
    expect(usePlayer.getState().playing).toBe(false);

    player.toggle(1, '/api/tracks/1/audio', 300); // playerul oprește previzualizarea
    expect(usePreview.getState().status).toBe('idle');
  });

  it('o eroare la încărcare revine la repaus', async () => {
    await transitionPreview.play('7/3', plan, async () => {
      throw new Error('404');
    });
    expect(usePreview.getState()).toMatchObject({ key: null, status: 'idle' });
  });
});
