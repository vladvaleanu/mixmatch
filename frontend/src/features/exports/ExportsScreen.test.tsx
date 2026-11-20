import { cleanup, screen, within } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';

import { ro } from '../../i18n/ro';
import { mockApi, renderWithProviders } from '../../testing';
import { ExportsScreen } from './ExportsScreen';

const base = {
  mix_id: 7,
  mix_name: 'Set de vineri',
  format: 'mp3',
  path: '/Users/tu/Music/mixmatch/Set de vineri/Set de vineri.mp3',
  duration_s: 2580,
  created_at: '2026-11-20T20:00:00Z',
  files: ['audio', 'tracklist', 'cue'],
};
const job = (status: string, progress = 1, error: string | null = null) => ({
  id: 1,
  kind: 'export',
  status,
  progress,
  error,
});

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

describe('Exporturi', () => {
  it('arată exporturile cu starea și descărcările', async () => {
    mockApi({
      'GET /api/exports': () => [
        { ...base, id: 3, job: job('running', 0.4), duration_s: null, files: [] },
        { ...base, id: 2, job: job('done') },
        { ...base, id: 1, mix_id: null, job: job('failed', 0.2, 'fișier lipsă'), files: [] },
      ],
    });
    renderWithProviders(<ExportsScreen />);

    const items = await screen.findAllByRole('listitem');
    expect(within(items[0] as HTMLElement).getByRole('progressbar')).toBeTruthy();
    expect(
      within(items[0] as HTMLElement).getByText(ro.screens.exports.rendering(40)),
    ).toBeTruthy();

    const done = within(items[1] as HTMLElement);
    expect(done.getByText(base.path)).toBeTruthy();
    expect(done.getByText(/MP3 · .* · 43 min/)).toBeTruthy();
    expect(
      done.getByRole('link', { name: ro.screens.exports.download.audio }).getAttribute('href'),
    ).toBe('/api/exports/2/file?kind=audio');
    expect(
      done.getByRole('link', { name: ro.screens.exports.download.cue }).getAttribute('href'),
    ).toBe('/api/exports/2/file?kind=cue');

    const failed = within(items[2] as HTMLElement);
    expect(failed.getByText(/fișier lipsă/)).toBeTruthy();
    expect(failed.getByText(new RegExp(ro.screens.exports.deletedMix))).toBeTruthy();
  });

  it('spune când nu există exporturi', async () => {
    mockApi({ 'GET /api/exports': () => [] });
    renderWithProviders(<ExportsScreen />);
    expect(await screen.findByText(ro.screens.exports.empty)).toBeTruthy();
  });
});
