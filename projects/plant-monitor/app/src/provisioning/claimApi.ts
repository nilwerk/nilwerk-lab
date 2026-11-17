// Cloud side of device setup: POST /claim-token (openapi.yaml) and the "devices row visible under RLS" check (ble-provisioning.md section 3 step 5).
// The access token and publishable key come from the build env / auth service, never from code. The claim token is a secret for 15 minutes:
// it is returned to the caller and never logged or put into an error message.
export type ClaimApiErrorCode = 'unauthorized' | 'rate_limited' | 'network' | 'server';
export class ClaimApiError extends Error {
  code: ClaimApiErrorCode;
  constructor(code: ClaimApiErrorCode, status?: number) { super(status ? `claim api: ${code} (${status})` : `claim api: ${code}`); this.name = 'ClaimApiError'; this.code = code; }
}

export interface ClaimApi {
  /** POST /claim-token -> 22-character base64url token (single use, 15 min). */
  issueClaimToken(): Promise<string>;
  /** The user's own devices row whose hw_id ends in the 6 hex of the advertised name (NW-xxxxxx), newest claim first; null when none is visible yet. */
  findClaimedDevice(advertisedName: string): Promise<{ deviceId: string; hwId: string } | null>;
}

export interface FetchClaimApiDeps {
  baseUrl: string;
  publishableKey: string;
  getAccessToken: () => Promise<string | null>;
  fetchImpl?: typeof fetch;
}

const TOKEN_RE = /^[A-Za-z0-9_-]{22}$/;
export const isClaimToken = (s: unknown): s is string => typeof s === 'string' && TOKEN_RE.test(s);

export function createFetchClaimApi(d: FetchClaimApiDeps): ClaimApi {
  const f = d.fetchImpl ?? fetch;
  const base = d.baseUrl.replace(/\/+$/, '');
  const call = async (path: string, init: RequestInit): Promise<Response> => {
    const token = await d.getAccessToken().catch(() => null);
    if (!token) throw new ClaimApiError('unauthorized');
    try {
      return await f(`${base}${path}`, { ...init, headers: { apikey: d.publishableKey, Authorization: `Bearer ${token}`, Accept: 'application/json' } });
    } catch { throw new ClaimApiError('network'); }
  };
  const fail = (r: Response): never => { throw new ClaimApiError(r.status === 401 ? 'unauthorized' : r.status === 429 ? 'rate_limited' : 'server', r.status); };
  return {
    async issueClaimToken() {
      const r = await call('/functions/v1/claim-token', { method: 'POST' });
      if (r.status !== 201) return fail(r);
      const body = (await r.json().catch(() => null)) as { claim_token?: unknown } | null;
      if (!isClaimToken(body?.claim_token)) throw new ClaimApiError('server', 201); // never accept a token the sensor would refuse
      return body.claim_token;
    },
    async findClaimedDevice(advertisedName) {
      const m = /^NW-([0-9a-f]{6})$/i.exec(advertisedName);
      if (!m) return null;
      const suffix = m[1].toLowerCase();
      const r = await call(`/rest/v1/devices?select=id,hw_id,claimed_at&hw_id=like.*${suffix}&order=claimed_at.desc.nullslast&limit=5`, { method: 'GET' });
      if (!r.ok) return fail(r);
      const rows = (await r.json().catch(() => [])) as { id?: unknown; hw_id?: unknown }[];
      const hit = Array.isArray(rows) ? rows.find((x) => typeof x.id === 'string' && typeof x.hw_id === 'string' && x.hw_id.endsWith(suffix)) : undefined;
      return hit ? { deviceId: hit.id as string, hwId: hit.hw_id as string } : null;
    },
  };
}
