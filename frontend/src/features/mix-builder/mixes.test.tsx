import { cleanup, fireEvent, screen, waitFor } from '@testing-library/react';
import { Route, Routes } from 'react-router-dom';
import { afterEach, describe, expect, it, vi } from 'vitest';

import { ro } from '../../i18n/ro';
import { mockApi, renderWithProviders } from '../../testing';
import { AddToMixButton } from '../library/AddToMixButton';
import { useActiveMix } from './activeMixStore';
import { MixBuilderScreen } from './MixBuilderScreen';
import { MixesScreen } from './MixesScreen';

function track(id: number, title: string) {
  return {
    id,
    title,
    artist: 'Artist',
    duration_s: 360,
    bpm: 120 + id,
    key_camelot: '8A',
    key_name: 'La minor',
    energy: 3,
    energy_manual: null,
    intro_bars: 16,
    outro_bars: 16,
    waveform_preview: null,
    analyzed: true,
  };
}

const a = track(1, 'Alfa');
const b = track(2, 'Beta');
const c = track(3, 'Gama');

function mix(tracks = [a, b, c], name = 'Set de vineri') {
  return {
    id: 7,
    name,
    energy_shape: 'free',
    duration_s: tracks.length * 360,
    updated_at: '2026-11-20T12:00:00Z',
    tracks,
  };
}

function report(tracks = [a, b, c], extra: object = {}) {
  return {
    mix_id: 7,
    track_ids: tracks.map((t) => t.id),
    energy_shape: 'free',
    transitions: tracks.slice(1).map((t, i) => ({
      position: i + 1,
      from_track_id: tracks[i]?.id,
      to_track_id: t.id,
      label: 'smooth',
      reason: '8A → 8A · +1 BPM',
      problem: null,
    })),
    energy: tracks.map((t) => ({ track_id: t.id, actual: 3, target: null })),
    next_target_energy: null,
    warnings: [],
    ...extra,
  };
}

async function body(api: ReturnType<typeof mockApi>, method: string, path: string) {
  const call = api.mock.calls
    .map(([req]) => req as Request)
    .filter((r) => r.method === method && new URL(r.url).pathname === path)
    .pop();
  return call ? await call.clone().json() : undefined;
}

function renderBuilder() {
  return renderWithProviders(
    <Routes>
      <Route path="/mixuri/:mixId" element={<MixBuilderScreen />} />
      <Route path="/mixuri" element={<p>lista</p>} />
    </Routes>,
    '/mixuri/7',
  );
}

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  useActiveMix.setState({ id: null });
});

describe('Mix-uri', () => {
  it('arată mixurile și creează unul nou', async () => {
    const api = mockApi({
      'GET /api/mixes': () => [
        {
          id: 7,
          name: 'Set de vineri',
          track_count: 7,
          duration_s: 2580,
          updated_at: '2026-11-20T12:00:00Z',
        },
      ],
      'POST /api/mixes': () => Response.json(mix([], 'Mix nou'), { status: 201 }),
      'GET /api/mixes/7': () => mix([], 'Mix nou'),
      'GET /api/mixes/7/report': () => report([]),
    });
    renderWithProviders(
      <Routes>
        <Route path="/mixuri" element={<MixesScreen />} />
        <Route path="/mixuri/:mixId" element={<MixBuilderScreen />} />
      </Routes>,
      '/mixuri',
    );

    expect(await screen.findByText('Set de vineri')).toBeTruthy();
    expect(screen.getByText(ro.mixes.meta(7, '43 min'))).toBeTruthy();

    fireEvent.click(screen.getByRole('button', { name: ro.mixes.create }));
    expect(await screen.findByDisplayValue('Mix nou')).toBeTruthy();
    expect(await body(api, 'POST', '/api/mixes')).toEqual({ name: 'Mix nou', track_ids: [] });
    expect(useActiveMix.getState().id).toBe(7);
  });
});

describe('Constructorul de mix', () => {
  it('arată piesele în ordine, cu meta', async () => {
    mockApi({ 'GET /api/mixes/7': () => mix() });
    renderBuilder();

    expect(await screen.findByDisplayValue('Set de vineri')).toBeTruthy();
    const titles = screen.getAllByRole('listitem').map((li) => li.textContent);
    expect(titles[0]).toContain('Alfa');
    expect(titles[2]).toContain('Gama');
    expect(screen.getByText(`${ro.mixes.meta(3, '18 min')} · 121 → 123 BPM`)).toBeTruthy();
    expect(useActiveMix.getState().id).toBe(7);
  });

  it('scoate o piesă și salvează noua ordine', async () => {
    const api = mockApi({
      'GET /api/mixes/7': () => mix(),
      'GET /api/mixes/7/report': () => report(),
      'GET /api/tracks/3/matches': () => [],
      'PUT /api/mixes/7/items': () => mix([a, c]),
    });
    renderBuilder();

    fireEvent.click(await screen.findByRole('button', { name: ro.builder.remove('Beta') }));

    await waitFor(() => expect(screen.queryByText('Beta')).toBeNull());
    expect(await body(api, 'PUT', '/api/mixes/7/items')).toEqual({ track_ids: [1, 3] });
  });

  it('adaugă o piesă din bibliotecă la final', async () => {
    const d = track(4, 'Delta');
    const api = mockApi({
      'GET /api/mixes/7': () => mix(),
      'GET /api/mixes/7/report': () => report(),
      'GET /api/tracks/3/matches': () => [],
      'GET /api/tracks': () => [a, d],
      'PUT /api/mixes/7/items': () => mix([a, b, c, d]),
    });
    renderBuilder();

    fireEvent.click(await screen.findByRole('button', { name: ro.builder.add }));
    expect(await screen.findByText(ro.builder.inMix)).toBeTruthy(); // Alfa e deja în mix
    fireEvent.click(screen.getByRole('button', { name: ro.builder.addOne('Delta') }));

    await waitFor(async () =>
      expect(await body(api, 'PUT', '/api/mixes/7/items')).toEqual({ track_ids: [1, 2, 3, 4] }),
    );
  });

  it('redenumește mixul', async () => {
    const api = mockApi({
      'GET /api/mixes/7': () => mix(),
      'GET /api/mixes/7/report': () => report(),
      'GET /api/tracks/3/matches': () => [],
      'PATCH /api/mixes/7': () => mix(undefined, 'Vârf de seară'),
    });
    renderBuilder();

    const input = await screen.findByLabelText(ro.builder.name);
    fireEvent.change(input, { target: { value: '  Vârf de seară ' } });
    fireEvent.blur(input);

    await waitFor(async () =>
      expect(await body(api, 'PATCH', '/api/mixes/7')).toEqual({ name: 'Vârf de seară' }),
    );
  });

  it('șterge mixul după confirmare', async () => {
    const api = mockApi({
      'GET /api/mixes/7': () => mix(),
      'GET /api/mixes/7/report': () => report(),
      'GET /api/tracks/3/matches': () => [],
      'DELETE /api/mixes/7': () => new Response(null, { status: 204 }),
    });
    renderBuilder();

    fireEvent.click(await screen.findByRole('button', { name: ro.builder.delete }));
    const dialog = await screen.findByRole('dialog');
    fireEvent.click(dialog.querySelectorAll('button')[1] as HTMLButtonElement);

    expect(await screen.findByText('lista')).toBeTruthy();
    expect(api.mock.calls.some(([r]) => (r as Request).method === 'DELETE')).toBe(true);
  });
});

describe('Raportul mixului', () => {
  it('arată etichetele dintre carduri și avertismentele', async () => {
    mockApi({
      'GET /api/mixes/7': () => mix(),
      'GET /api/tracks/3/matches': () => [],
      'GET /api/mixes/7/report': () => {
        const r = report();
        const second = r.transitions[1];
        if (second) Object.assign(second, { label: 'caution', problem: 'key', reason: '8A → 3B' });
        return {
          ...r,
          warnings: [
            {
              position: 2,
              problem: 'key',
              message: 'Între „Beta” și „Gama” tonalitățile se ciocnesc.',
            },
          ],
        };
      },
    });
    renderBuilder();

    expect(await screen.findByRole('alert')).toHaveProperty(
      'textContent',
      'Între „Beta” și „Gama” tonalitățile se ciocnesc.',
    );
    const notes = screen.getAllByRole('note').map((n) => n.getAttribute('aria-label'));
    expect(notes).toEqual([
      ro.report.transition('Alfa', 'Beta', ro.transition.smooth, '8A → 8A · +1 BPM'),
      ro.report.transition('Beta', 'Gama', ro.transition.caution, '8A → 3B'),
    ]);
  });

  it('schimbă forma setului', async () => {
    const api = mockApi({
      'GET /api/mixes/7': () => mix(),
      'GET /api/mixes/7/report': () => report(),
      'GET /api/tracks/3/matches': () => [],
      'PATCH /api/mixes/7': () => ({ ...mix(), energy_shape: 'rise' }),
    });
    renderBuilder();

    fireEvent.click(await screen.findByRole('button', { name: ro.report.shapes.rise }));
    await waitFor(async () =>
      expect(await body(api, 'PATCH', '/api/mixes/7')).toEqual({ energy_shape: 'rise' }),
    );
    expect(
      (await screen.findByRole('button', { name: ro.report.shapes.rise })).getAttribute(
        'aria-pressed',
      ),
    ).toBe('true');
  });

  it('sugerează ce urmează după ultima piesă și o adaugă', async () => {
    const d = track(4, 'Delta');
    const api = mockApi({
      'GET /api/mixes/7': () => mix(),
      'GET /api/mixes/7/report': () => report(undefined, { next_target_energy: 4.5 }),
      'GET /api/tracks/3/matches': () => [
        { track: d, label: 'good', score: 80, reason: '8A → 10A · +1 BPM' },
      ],
      'PUT /api/mixes/7/items': () => mix([a, b, c, d]),
    });
    renderBuilder();

    expect(await screen.findByText(ro.report.next('Gama'))).toBeTruthy();
    fireEvent.click(await screen.findByRole('button', { name: ro.report.addSuggestion('Delta') }));
    await waitFor(async () =>
      expect(await body(api, 'PUT', '/api/mixes/7/items')).toEqual({ track_ids: [1, 2, 3, 4] }),
    );
    const query = api.mock.calls
      .map(([r]) => new URL((r as Request).url))
      .filter((u) => u.pathname === '/api/tracks/3/matches')
      .pop()?.searchParams;
    expect(query?.get('exclude_mix')).toBe('7');
    expect(query?.get('target_energy')).toBe('4.5');
  });
});

describe('Adaugă în mix (Biblioteca)', () => {
  const summary = {
    id: 7,
    name: 'Set de vineri',
    track_count: 2,
    duration_s: 720,
    updated_at: '2026-11-20T12:00:00Z',
  };

  it('adaugă piesa la finalul mixului activ', async () => {
    useActiveMix.setState({ id: 7 });
    const d = track(4, 'Delta');
    const api = mockApi({
      'GET /api/mixes': () => [summary],
      'GET /api/mixes/7': () => mix([a, b]),
      'PUT /api/mixes/7/items': () => mix([a, b, d]),
    });
    renderWithProviders(<AddToMixButton track={d} />);

    fireEvent.click(await screen.findByRole('button', { name: ro.addToMix.add('Set de vineri') }));

    expect(
      await screen.findByRole('button', { name: ro.addToMix.already('Set de vineri') }),
    ).toBeTruthy();
    expect(await body(api, 'PUT', '/api/mixes/7/items')).toEqual({ track_ids: [1, 2, 4] });
  });

  it('fără mixuri, creează unul nou cu piesa', async () => {
    const api = mockApi({
      'GET /api/mixes': () => [],
      'POST /api/mixes': () => Response.json(mix([a], 'Mix nou'), { status: 201 }),
    });
    renderWithProviders(<AddToMixButton track={a} />);

    fireEvent.click(await screen.findByRole('button', { name: ro.addToMix.addNew }));

    await waitFor(() => expect(useActiveMix.getState().id).toBe(7));
    expect(await body(api, 'POST', '/api/mixes')).toEqual({ name: 'Mix nou', track_ids: [1] });
  });
});
