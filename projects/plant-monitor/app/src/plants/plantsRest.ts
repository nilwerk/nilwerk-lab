// Thin PostgREST / Storage client with fetch (same pattern as export/exportClient.ts, so no second Supabase client and no shared session).
// Requirements: FR-A06 (list, detail, hourly), FR-A05 (photos, no cap), FR-A08 + NFR-07 (delete_plant, photo objects), NFR-06 (user JWT -> RLS applies).
// NOT run against a real backend (no project exists, A-025); unit-tested with a fake fetch only.
import { PlantsError } from './types';

export interface RestDeps { baseUrl: string; publishableKey: string; getAccessToken: () => Promise<string | null>; fetchImpl?: typeof fetch }

/** Supabase caps a response at 1000 rows by default; FR-A02 / FR-A05 say no cap, so lists are paged with Range. */
export const PAGE = 1000;
const MAX_PAGES = 100;

const root = (d: RestDeps) => d.baseUrl.replace(/\/+$/, '');

export async function call(d: RestDeps, path: string, init: { method?: string; body?: unknown; range?: [number, number]; prefer?: string } = {}): Promise<{ status: number; json: unknown }> {
  const token = await d.getAccessToken().catch(() => null);
  if (!token) throw new PlantsError('unknown', 'not signed in');
  const headers: Record<string, string> = { Authorization: `Bearer ${token}`, apikey: d.publishableKey, Accept: 'application/json' };
  if (init.body !== undefined) headers['Content-Type'] = 'application/json';
  if (init.range) { headers['Range-Unit'] = 'items'; headers.Range = `${init.range[0]}-${init.range[1]}`; }
  if (init.prefer) headers.Prefer = init.prefer; // e.g. return=representation, so a write answers with the row
  let res: Response;
  try {
    res = await (d.fetchImpl ?? fetch)(`${root(d)}${path}`, { method: init.method ?? 'GET', headers, body: init.body === undefined ? undefined : JSON.stringify(init.body) });
  } catch {
    throw new PlantsError('network');
  }
  let json: unknown = null;
  try { json = await res.json(); } catch { json = null; }
  if (res.status >= 200 && res.status < 300) return { status: res.status, json };
  // 'plant not found' is raised with errcode P0002 by delete_plant (same answer for unknown and foreign ids)
  const code = (json as { code?: unknown } | null)?.code;
  if (code === 'P0002' || res.status === 404) throw new PlantsError('not_found');
  throw new PlantsError(res.status >= 500 ? 'network' : 'unknown', `HTTP ${res.status}`);
}

/** GET a table/view, every page. A non-array body is an error (never "empty list"). */
export async function selectAll(d: RestDeps, pathAndQuery: string): Promise<Record<string, unknown>[]> {
  const out: Record<string, unknown>[] = [];
  for (let p = 0; p < MAX_PAGES; p++) {
    const { json } = await call(d, `/rest/v1/${pathAndQuery}`, { range: [p * PAGE, p * PAGE + PAGE - 1] });
    if (!Array.isArray(json)) throw new PlantsError('unknown', 'unexpected response');
    out.push(...(json as Record<string, unknown>[]));
    if (json.length < PAGE) return out;
  }
  throw new PlantsError('unknown', 'too many rows');
}

export async function rpc(d: RestDeps, fn: string, args: Record<string, unknown>): Promise<unknown> {
  return (await call(d, `/rest/v1/rpc/${fn}`, { method: 'POST', body: args })).json;
}

/** Storage: remove objects from one bucket. Returns the names the server reports as removed (a missing object is simply absent from it). */
export async function removeObjects(d: RestDeps, bucket: string, paths: string[]): Promise<string[]> {
  const { json } = await call(d, `/storage/v1/object/${bucket}`, { method: 'DELETE', body: { prefixes: paths } });
  if (!Array.isArray(json)) throw new PlantsError('unknown', 'unexpected response');
  return json.map((o) => (o as { name?: unknown })?.name).filter((n): n is string => typeof n === 'string');
}
