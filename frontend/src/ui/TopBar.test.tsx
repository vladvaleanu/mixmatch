import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { cleanup, render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { afterEach, describe, expect, it, vi } from 'vitest';

import { ro } from '../i18n/ro';
import { TopBar } from './TopBar';

function renderTopBar(path: string) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={[path]}>
        <TopBar />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

describe('TopBar', () => {
  it('marchează secțiunea curentă și arată serverul conectat', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async () => new Response(JSON.stringify({ status: 'ok', version: '0.1.0' }))),
    );
    renderTopBar('/mixuri');

    const active = screen.getByRole('link', { name: ro.nav.mixes });
    expect(active.getAttribute('aria-current')).toBe('page');
    expect(screen.getByRole('link', { name: ro.nav.library }).getAttribute('aria-current')).toBe(
      null,
    );
    expect(await screen.findByText(ro.health.ok)).toBeTruthy();
  });

  it('arată când serverul nu răspunde', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async () => new Response('', { status: 502 })),
    );
    renderTopBar('/biblioteca');

    expect(await screen.findByText(ro.health.down)).toBeTruthy();
  });
});
