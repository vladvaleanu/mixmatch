import { cleanup, fireEvent, screen, waitFor } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';

import { ro } from '../../i18n/ro';
import { mockApi, renderWithProviders } from '../../testing';
import { Toast } from '../../ui/Toast';
import { useToastStore } from '../../ui/toastStore';
import { LibraryScreen } from './LibraryScreen';
import { useAddFolderDialog } from './addFolderStore';
import { useSelectedTrack } from './selectionStore';

const track = {
  id: 1,
  title: 'Paper Lights',
  artist: 'Oda Kray',
  duration_s: 348,
  bpm: 124,
  key_camelot: '8A',
  key_name: 'La minor',
  energy: 3,
  energy_manual: null as number | null,
  intro_bars: 16,
  outro_bars: 32,
  waveform_preview: Array.from({ length: 40 }, (_, i) => i * 6),
  analyzed: true,
};
const pending = {
  ...track,
  bpm: null,
  key_camelot: null,
  key_name: null,
  energy: null,
  waveform_preview: null,
  analyzed: false,
};
const noJobs = { 'GET /api/jobs/active': () => [] };

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  useAddFolderDialog.setState({ open: false });
  useToastStore.setState({ message: null });
  useSelectedTrack.setState({ id: null });
});

describe('LibraryScreen', () => {
  it('arată piesele cu artist, BPM, ton și durată', async () => {
    mockApi({ ...noJobs, 'GET /api/tracks': () => [track, { ...track, id: 2, artist: null }] });
    renderWithProviders(<LibraryScreen />);

    expect(await screen.findAllByText('Paper Lights')).toHaveLength(2);
    expect(screen.getByText('Oda Kray')).toBeTruthy();
    expect(screen.getByText(ro.library.unknownArtist)).toBeTruthy();
    expect(screen.getAllByText('5:48')).toHaveLength(2);
    expect(screen.getByText(ro.library.trackCount(2))).toBeTruthy();
    expect(screen.getAllByText('124')).toHaveLength(2);
    expect(screen.getAllByLabelText('Ton 8A, La minor')).toHaveLength(2);
  });

  it('corectează energia din tabel și revine la automat', async () => {
    let current = { ...track };
    const patches: unknown[] = [];
    mockApi({
      ...noJobs,
      'GET /api/tracks': () => [current],
      'PATCH /api/tracks/1': async (request) => {
        const body = (await request.json()) as { energy_manual: number | null };
        patches.push(body);
        current = { ...track, energy: body.energy_manual ?? 3, energy_manual: body.energy_manual };
        return current;
      },
    });
    renderWithProviders(<LibraryScreen />);

    fireEvent.click(await screen.findByRole('radio', { name: ro.energy.set(5) }));
    await screen.findByRole('radiogroup', { name: ro.energy.label(5, true) });

    fireEvent.click(screen.getByRole('radio', { name: ro.energy.set(5) }));
    await screen.findByRole('radiogroup', { name: ro.energy.label(3, false) });
    expect(patches).toEqual([{ energy_manual: 5 }, { energy_manual: null }]);
  });

  it('selectează o piesă și îi arată detaliile în panou', async () => {
    mockApi({
      ...noJobs,
      'GET /api/tracks': () => [track],
      'GET /api/tracks/1/waveform': () => ({ peaks: Array.from({ length: 1000 }, () => 128) }),
    });
    renderWithProviders(<LibraryScreen />);
    expect(await screen.findByText(ro.panel.empty)).toBeTruthy();

    fireEvent.click(await screen.findByRole('button', { name: 'Paper Lights' }));

    expect(screen.getByText(ro.panel.selected)).toBeTruthy();
    expect(screen.getByText('124 BPM')).toBeTruthy();
    expect(screen.getByText('8A · La minor')).toBeTruthy();
    expect(screen.getByText(ro.panel.bars(16, 32))).toBeTruthy();
    expect(await screen.findByRole('slider', { name: ro.player.seek })).toBeTruthy();
  });

  it('marchează piesele neanalizate și arată progresul analizei', async () => {
    mockApi({
      'GET /api/tracks': () => [pending],
      'GET /api/jobs/active': () => [
        { id: 3, kind: 'analysis', status: 'running', progress: 0.25, error: null },
      ],
    });
    renderWithProviders(<LibraryScreen />);

    expect(await screen.findByText(`${ro.analysis.running} 25%`)).toBeTruthy();
    expect(screen.getAllByLabelText(ro.analysis.pending)).toHaveLength(3); // BPM, ton, energie
    expect(screen.queryByText('8A')).toBeNull();
  });

  it('adaugă un folder, urmărește scanarea și reîncarcă piesele', async () => {
    let scanned = false;
    let polls = 0;
    const api = mockApi({
      ...noJobs,
      'GET /api/tracks': () => (scanned ? [track] : []),
      'POST /api/library/folders': () =>
        Response.json({ folder_id: 1, job_id: 7 }, { status: 202 }),
      'GET /api/jobs/7': () => {
        polls += 1;
        if (polls < 2)
          return { id: 7, kind: 'scan', status: 'running', progress: 0.5, error: null };
        scanned = true;
        return { id: 7, kind: 'scan', status: 'done', progress: 1, error: null };
      },
    });
    renderWithProviders(<LibraryScreen />);
    expect(await screen.findByText(ro.library.empty)).toBeTruthy();

    fireEvent.click(screen.getByRole('button', { name: ro.library.addFolderZone }));
    const input = screen.getByLabelText(ro.addFolder.pathLabel);
    fireEvent.change(input, { target: { value: '  /Users/tu/Music  ' } });
    fireEvent.click(screen.getByRole('button', { name: ro.addFolder.submit }));

    expect(await screen.findByRole('progressbar')).toBeTruthy();
    expect(await screen.findByText(ro.addFolder.done(1), {}, { timeout: 3000 })).toBeTruthy();

    const post = api.mock.calls.map(([req]) => req as Request).find((r) => r.method === 'POST');
    expect(await post?.json()).toEqual({ path: '/Users/tu/Music' });

    fireEvent.click(screen.getByRole('button', { name: ro.common.close }));
    await waitFor(() => expect(screen.queryByRole('dialog')).toBeNull());
    expect(screen.getByText('Paper Lights')).toBeTruthy();
  });

  it('arată eroarea API în toast-ul global', async () => {
    mockApi({
      ...noJobs,
      'GET /api/tracks': () => [],
      'POST /api/library/folders': () =>
        Response.json(
          { error: { code: 'folder_not_found', message: 'Folderul nu există: /x' } },
          { status: 400 },
        ),
    });
    renderWithProviders(
      <>
        <LibraryScreen />
        <Toast />
      </>,
    );
    await screen.findByText(ro.library.empty);

    fireEvent.click(screen.getByRole('button', { name: ro.library.addFolderZone }));
    fireEvent.change(screen.getByLabelText(ro.addFolder.pathLabel), { target: { value: '/x' } });
    fireEvent.click(screen.getByRole('button', { name: ro.addFolder.submit }));

    expect((await screen.findByRole('alert')).textContent).toContain('Folderul nu există: /x');
    expect(screen.getByRole('dialog')).toBeTruthy(); // dialogul rămâne deschis pentru corectură
  });
});
