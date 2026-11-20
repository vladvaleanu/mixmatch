// Singurul loc din frontend care face cereri HTTP către backend.
// Tipurile vin din schema.d.ts (make types); nimic nu se scrie de mână.
import createClient from 'openapi-fetch';

import { ro } from '../i18n/ro';
import type { components, paths } from './schema';

export type Schemas = components['schemas'];

export const http = createClient<paths>({
  baseUrl: window.location.origin,
  // Caută `fetch` la fiecare cerere (nu o dată, la import), ca testele să-l poată înlocui.
  fetch: (request) => globalThis.fetch(request),
});

export class ApiError extends Error {
  constructor(
    readonly code: string,
    message: string,
    readonly status: number,
  ) {
    super(message);
  }
}

function isErrorBody(value: unknown): value is Schemas['ErrorBody'] {
  return typeof value === 'object' && value !== null && 'error' in value;
}

/** Întoarce `data` sau aruncă un ApiError cu codul și mesajul din `{"error": {...}}`. */
export async function unwrap<T>(
  request: Promise<{ data?: T; error?: unknown; response: Response }>,
): Promise<T> {
  let result: Awaited<typeof request>;
  try {
    result = await request;
  } catch {
    throw new ApiError('network', ro.errors.network, 0);
  }
  const { data, error, response } = result;
  if (error !== undefined || data === undefined) {
    if (isErrorBody(error)) {
      throw new ApiError(error.error.code, error.error.message, response.status);
    }
    throw new ApiError(`http_${response.status}`, ro.errors.unexpected, response.status);
  }
  return data;
}
