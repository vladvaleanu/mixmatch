import { cleanup, screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';

import { ro } from '../i18n/ro';
import { mockApi, renderWithProviders } from '../testing';
import { TopBar } from './TopBar';

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

describe('TopBar', () => {
  it('marchează secțiunea curentă și arată serverul conectat', async () => {
    mockApi({ 'GET /api/health': () => ({ status: 'ok', version: '0.1.0' }) });
    renderWithProviders(<TopBar />, '/mixuri');

    const active = screen.getByRole('link', { name: ro.nav.mixes });
    expect(active.getAttribute('aria-current')).toBe('page');
    expect(screen.getByRole('link', { name: ro.nav.library }).getAttribute('aria-current')).toBe(
      null,
    );
    expect(await screen.findByText(ro.health.ok)).toBeTruthy();
  });

  it('arată când serverul nu răspunde, fără toast', async () => {
    mockApi({ 'GET /api/health': () => new Response('', { status: 502 }) });
    renderWithProviders(<TopBar />, '/biblioteca');

    expect(await screen.findByText(ro.health.down)).toBeTruthy();
  });
});
