import { cleanup, fireEvent, screen, waitFor } from '@testing-library/react';
import { Route, Routes } from 'react-router-dom';
import { afterEach, describe, expect, it, vi } from 'vitest';

import { ro } from '../../i18n/ro';
import { mockApi, renderWithProviders } from '../../testing';
import { TransitionScreen } from './TransitionScreen';

function track(id: number, title: string, bpm: number, key: string, energy: number) {
  return {
    id,
    title,
    artist: 'Artist',
    duration_s: 360,
    bpm,
    key_camelot: key,
    key_name: null,
    energy,
    energy_manual: null,
    intro_bars: 16,
    outro_bars: 32,
    waveform_preview: null,
    analyzed: true,
  };
}

function transition(plan: object = {}) {
  return {
    mix_id: 7,
    mix_name: 'Set de vineri',
    position: 3,
    track_count: 7,
    from_track: track(1, 'Slow Orbit', 123, '9A', 3),
    to_track: track(2, 'Paper Lights', 124, '8A', 4),
    label: 'smooth',
    reason: '9A → 8A · +1 BPM',
    problem: null,
    key_label: 'smooth',
    tempo_label: 'smooth',
    energy_label: 'smooth',
    key_after_sync: '8A',
    plan: {
      style: 'eq_swap',
      length_bars: 16,
      length_s: 31.2,
      a_out_s: 290,
      b_in_s: 0.3,
      a_start_s: 290,
      b_start_s: 0.3,
      speed_b: 123 / 124,
      gain_a_db: -2,
      gain_b_db: 1,
      echo_delay_s: 0.36,
      echo_feedback: 0.45,
      automations: [
        {
          target: 'a_volume',
          points: [
            { t_s: 0, value: 1 },
            { t_s: 15.6, value: 1 },
            { t_s: 31.2, value: 0 },
          ],
        },
        {
          target: 'b_volume',
          points: [
            { t_s: 0, value: 0 },
            { t_s: 15.6, value: 1 },
            { t_s: 31.2, value: 1 },
          ],
        },
        {
          target: 'a_bass',
          points: [
            { t_s: 0, value: 0 },
            { t_s: 15.6, value: 0 },
            { t_s: 15.6, value: -26 },
          ],
        },
      ],
      a_out_auto: true,
      b_in_auto: true,
      ...plan,
    },
  };
}

function render() {
  return renderWithProviders(
    <Routes>
      <Route path="/mixuri/:mixId/tranzitii/:position" element={<TransitionScreen />} />
    </Routes>,
    '/mixuri/7/tranzitii/3',
  );
}

async function lastPatch(api: ReturnType<typeof mockApi>) {
  const call = api.mock.calls
    .map(([r]) => r as Request)
    .filter((r) => r.method === 'PATCH')
    .pop();
  return call ? await call.clone().json() : undefined;
}

const waves = {
  'GET /api/tracks/1/waveform': () => ({ peaks: Array.from({ length: 8000 }, () => 128) }),
  'GET /api/tracks/2/waveform': () => ({ peaks: Array.from({ length: 8000 }, () => 200) }),
};

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

describe('Editorul de tranziție', () => {
  it('arată perechea, chip-urile și suprapunerea', async () => {
    mockApi({ ...waves, 'GET /api/mixes/7/transitions/3/plan': () => transition() });
    render();

    expect(await screen.findByText('Slow Orbit → Paper Lights')).toBeTruthy();
    expect(screen.getByText(ro.transitionEditor.heading(3, 4))).toBeTruthy();
    expect(screen.getByText('Ton 9A → 8A · compatibil')).toBeTruthy();
    expect(screen.getByText('Tempo 123 → 124 · B la −0,8 %')).toBeTruthy();
    expect(screen.getByText('Energie 3 → 4 · urcă')).toBeTruthy();
    expect(screen.getByText(ro.transitionEditor.overlap(16, 31))).toBeTruthy();
    expect(screen.getByText(ro.transitionEditor.lines.bass)).toBeTruthy();
    expect(screen.getByRole('button', { name: '16' }).getAttribute('aria-pressed')).toBe('true');
  });

  it('schimbă lungimea, stilul și punctele, și alege automat', async () => {
    const api = mockApi({
      ...waves,
      'GET /api/mixes/7/transitions/3/plan': () => transition(),
      'PATCH /api/mixes/7/transitions/3': () => transition({ length_bars: 32, length_s: 62.4 }),
    });
    render();

    fireEvent.click(await screen.findByRole('button', { name: '32' }));
    await waitFor(async () => expect(await lastPatch(api)).toEqual({ length_bars: 32 }));
    expect((await screen.findByRole('button', { name: '32' })).getAttribute('aria-pressed')).toBe(
      'true',
    );

    fireEvent.click(screen.getByRole('radio', { name: /Ieșire cu ecou/ }));
    await waitFor(async () => expect(await lastPatch(api)).toEqual({ style: 'echo_out' }));

    fireEvent.click(
      screen.getByRole('button', { name: ro.transitionEditor.later(ro.transitionEditor.aOut) }),
    );
    await waitFor(async () =>
      expect((await lastPatch(api)).a_out_s).toBeCloseTo(290 + 8 * (240 / 123), 3),
    );

    fireEvent.click(screen.getByRole('button', { name: ro.transitionEditor.auto }));
    await waitFor(async () => expect(await lastPatch(api)).toEqual({ auto: true }));
  });

  it('explică de ce nu se poate planifica', async () => {
    mockApi({
      'GET /api/mixes/7/transitions/3/plan': () =>
        Response.json(
          { error: { code: 'not_analyzed', message: ro.transitionEditor.notAnalyzed } },
          { status: 409 },
        ),
    });
    render();
    expect(await screen.findAllByText(ro.transitionEditor.notAnalyzed)).not.toHaveLength(0);
  });
});
