import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { player, usePlayer } from './engine';

class FakeAudioContext {
  resume = vi.fn(async () => undefined);
  destination = {};
  createMediaElementSource() {
    return { connect: vi.fn() };
  }
}

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
