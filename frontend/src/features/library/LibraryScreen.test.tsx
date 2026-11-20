import { cleanup, fireEvent, screen, waitFor } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';

import { ro } from '../../i18n/ro';
import { mockApi, renderWithProviders } from '../../testing';
import { Toast } from '../../ui/Toast';
import { useToastStore } from '../../ui/toastStore';
import { LibraryScreen } from './LibraryScreen';
import { useAddFolderDialog } from './addFolderStore';

const track = { id: 1, title: 'Paper Lights', artist: 'Oda Kray', duration_s: 348 };

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  useAddFolderDialog.setState({ open: false });
  useToastStore.setState({ message: null });
});

describe('LibraryScreen', () => {
  it('arată piesele cu artist și durată', async () => {
    mockApi({ 'GET /api/tracks': () => [track, { ...track, id: 2, artist: null }] });
    renderWithProviders(<LibraryScreen />);

    expect(await screen.findAllByText('Paper Lights')).toHaveLength(2);
    expect(screen.getByText('Oda Kray')).toBeTruthy();
    expect(screen.getByText(ro.library.unknownArtist)).toBeTruthy();
    expect(screen.getAllByText('5:48')).toHaveLength(2);
    expect(screen.getByText(ro.library.trackCount(2))).toBeTruthy();
  });

  it('adaugă un folder, urmărește scanarea și reîncarcă piesele', async () => {
    let scanned = false;
    let polls = 0;
    const api = mockApi({
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
