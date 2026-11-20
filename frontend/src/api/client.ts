// Singurul loc din frontend care face cereri HTTP către backend.
import type { paths } from './schema';

type GetPath = { [P in keyof paths]: paths[P] extends { get: unknown } ? P : never }[keyof paths];

type GetResponse<P extends GetPath> = paths[P] extends {
  get: { responses: { 200: { content: { 'application/json': infer T } } } };
}
  ? T
  : never;

export async function apiGet<P extends GetPath>(path: P): Promise<GetResponse<P>> {
  const response = await fetch(path);
  if (!response.ok) {
    throw new Error(`${response.status} ${response.statusText}`);
  }
  return (await response.json()) as GetResponse<P>;
}
