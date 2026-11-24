// Client for the personal MCP API keys (task 4.A8). Contract: docs/interfaces/openapi.yaml /api-keys (POST create, DELETE /api-keys/{id} revoke) and
// docs/interfaces/db-schema.sql public.api_keys (list = select of the granted columns under RLS, never the key or its hash).
// Requirements: FR-P03 (generate / revoke a key for the user's AI), FR-P04 (403 premium_required: free accounts get no key), NFR-06 (user JWT; the key is
// returned once by the server, only its hash and prefix are stored; this client never persists it).
// The edge function route name `api-keys` is PROPOSED: the function is not built yet (cloud/supabase/functions has no api-keys). Unit-tested with a fake fetch only.
export type ApiKeysErrorCode = 'premium_required' | 'unauthorized' | 'not_found' | 'network' | 'server' | 'bad_response' | 'not_configured' | 'unknown';

export class ApiKeysError extends Error {
  code: ApiKeysErrorCode;
  constructor(code: ApiKeysErrorCode) {
    super(`api-keys: ${code}`);
    this.name = 'ApiKeysError';
    this.code = code;
  }
}

/** A listed key. Never carries the key itself (FR-P03). */
export interface ApiKeyInfo { id: string; name: string; prefix: string; createdAt: string; lastUsedAt: string | null; revokedAt: string | null }
/** The one-time result of creating a key. `key` is shown once and not stored anywhere. */
export interface CreatedApiKey { id: string; key: string; prefix: string }

export interface ApiKeysService {
  list(): Promise<ApiKeyInfo[]>;
  create(name: string): Promise<CreatedApiKey>;
  revoke(id: string): Promise<void>;
}

export interface ApiKeysClientDeps { baseUrl: string; publishableKey: string; getAccessToken: () => Promise<string | null>; fetchImpl?: typeof fetch }

const root = (b: string) => b.replace(/\/+$/, '');
export const apiKeysUrl = (baseUrl: string, id?: string): string => `${root(baseUrl)}/functions/v1/api-keys${id ? `/${encodeURIComponent(id)}` : ''}`;
export const apiKeysListUrl = (baseUrl: string): string =>
  `${root(baseUrl)}/rest/v1/api_keys?select=id,name,prefix,created_at,last_used_at,revoked_at&order=created_at.desc`;

const str = (v: unknown): string | null => (typeof v === 'string' && v ? v : null);

function parseInfo(row: unknown): ApiKeyInfo | null {
  const r = row as Record<string, unknown> | null;
  const id = str(r?.id), name = str(r?.name), prefix = str(r?.prefix), createdAt = str(r?.created_at);
  if (!r || !id || !name || !prefix || !createdAt) return null;
  return { id, name, prefix, createdAt, lastUsedAt: str(r.last_used_at), revokedAt: str(r.revoked_at) };
}

export function createApiKeysClient(d: ApiKeysClientDeps): ApiKeysService {
  const send = async (url: string, init: { method: string; body?: unknown }): Promise<Response> => {
    const token = await d.getAccessToken().catch(() => null);
    if (!token) throw new ApiKeysError('unauthorized');
    const headers: Record<string, string> = { Authorization: `Bearer ${token}`, apikey: d.publishableKey, Accept: 'application/json' };
    if (init.body !== undefined) headers['Content-Type'] = 'application/json';
    try {
      return await (d.fetchImpl ?? fetch)(url, { method: init.method, headers, body: init.body === undefined ? undefined : JSON.stringify(init.body) });
    } catch {
      throw new ApiKeysError('network');
    }
  };
  const fail = (status: number): ApiKeysError =>
    new ApiKeysError(status === 403 ? 'premium_required' : status === 401 ? 'unauthorized' : status === 404 ? 'not_found' : status >= 500 ? 'server' : 'unknown');

  return {
    async list() {
      const res = await send(apiKeysListUrl(d.baseUrl), { method: 'GET' });
      if (res.status !== 200) throw fail(res.status);
      let json: unknown;
      try { json = await res.json(); } catch { throw new ApiKeysError('bad_response'); }
      if (!Array.isArray(json)) throw new ApiKeysError('bad_response');
      const out = json.map(parseInfo);
      if (out.some((k) => k === null)) throw new ApiKeysError('bad_response');
      return out as ApiKeyInfo[];
    },
    async create(name) {
      const res = await send(apiKeysUrl(d.baseUrl), { method: 'POST', body: { name } });
      if (res.status !== 201) throw fail(res.status);
      let json: unknown;
      try { json = await res.json(); } catch { throw new ApiKeysError('bad_response'); }
      const r = json as Record<string, unknown> | null;
      const id = str(r?.id), key = str(r?.key), prefix = str(r?.prefix);
      if (!id || !key || !prefix) throw new ApiKeysError('bad_response');
      return { id, key, prefix };
    },
    async revoke(id) {
      const res = await send(apiKeysUrl(d.baseUrl, id), { method: 'DELETE' });
      if (res.status !== 204) throw fail(res.status);
    },
  };
}

/** Used when no backend is configured (or in the mock build): every call reports not_configured, nothing is fetched. */
export const unconfiguredApiKeys: ApiKeysService = {
  list: async () => { throw new ApiKeysError('not_configured'); },
  create: async () => { throw new ApiKeysError('not_configured'); },
  revoke: async () => { throw new ApiKeysError('not_configured'); },
};
