import { describe, expect, it } from 'vitest';

import { formatBpm, formatDuration } from './format';

describe('formatDuration', () => {
  it.each([
    [0, '0:00'],
    [59.6, '1:00'],
    [312.4, '5:12'],
    [3725, '1:02:05'],
  ])('%s s → %s', (seconds, expected) => {
    expect(formatDuration(seconds)).toBe(expected);
  });
});

describe('formatBpm', () => {
  it.each([
    [124, '124'],
    [123.5, '123,5'],
    [87.6, '87,6'],
  ])('%s → %s', (bpm, expected) => {
    expect(formatBpm(bpm)).toBe(expected);
  });
});
