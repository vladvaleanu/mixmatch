// Unelte comune pentru testele de componente.
import { QueryClientProvider } from '@tanstack/react-query';
import { render } from '@testing-library/react';
import type { ReactNode } from 'react';
import { MemoryRouter } from 'react-router-dom';
import { vi } from 'vitest';

import { createQueryClient } from './api/queryClient';

type Handler = (request: Request) => unknown | Response;

/** Înlocuiește `fetch` cu răspunsuri pe rute: { 'GET /api/tracks': () => [...] }. */
export function mockApi(routes: Record<string, Handler>) {
  const fetchMock = vi.fn(async (input: RequestInfo | URL) => {
    const request = input instanceof Request ? input : new Request(input);
    const key = `${request.method} ${new URL(request.url).pathname}`;
    const handler = routes[key];
    if (!handler) return new Response('', { status: 404 });
    const result = await handler(request);
    return result instanceof Response ? result : Response.json(result);
  });
  vi.stubGlobal('fetch', fetchMock);
  return fetchMock;
}

export function renderWithProviders(ui: ReactNode, path = '/') {
  const client = createQueryClient();
  client.setDefaultOptions({ queries: { retry: false } });
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={[path]}>{ui}</MemoryRouter>
    </QueryClientProvider>,
  );
}
