// Client for /api-keys (4.A8): request shapes against docs/interfaces/openapi.yaml and db-schema.sql, error mapping, and no secret handling beyond the one-time result.
// Requirements: FR-P03, FR-P04 (403 premium_required), NFR-06 (user JWT sent; key never logged or stored). Fake fetch only, no network.
import { createApiKeysClient, apiKeysUrl, apiKeysListUrl, ApiKeysError, unconfiguredApiKeys } from '../mcp/apiKeysApi';
import { validateKeyName } from '../mcp/keyName';

const base = 'https://example.invalid';
const res = (status: number, body?: unknown) => ({ status, json: async () => { if (body === undefined) throw new Error('no body'); return body; } }) as unknown as Response;
const client = (f: jest.Mock, token: string | null = 'jwt-test') => createApiKeysClient({ baseUrl: `${base}/`, publishableKey: 'pub-test', getAccessToken: async () => token, fetchImpl: f as unknown as typeof fetch });
const row = { id: 'k-1', name: 'n', prefix: 'nwk_TEST', created_at: '2026-11-24T10:00:00Z', last_used_at: null, revoked_at: null };
const code = async (p: Promise<unknown>) => p.then(() => 'resolved', (e) => (e as ApiKeysError).code);

describe('api keys client', () => {
  test('create: POST /functions/v1/api-keys with {name}, user JWT, returns id/key/prefix on 201', async () => {
    const f = jest.fn(async () => res(201, { id: 'k-1', key: 'nwk_TESTONLY', prefix: 'nwk_TEST' }));
    expect(await client(f).create('Laptop')).toEqual({ id: 'k-1', key: 'nwk_TESTONLY', prefix: 'nwk_TEST' });
    const [url, init] = f.mock.calls[0] as unknown as [string, RequestInit];
    expect(url).toBe(`${base}/functions/v1/api-keys`);
    expect(url).toBe(apiKeysUrl(base));
    expect(init.method).toBe('POST');
    expect(JSON.parse(init.body as string)).toEqual({ name: 'Laptop' });
    expect(init.headers).toMatchObject({ Authorization: 'Bearer jwt-test', apikey: 'pub-test' });
  });

  test('create: 403 is premium_required, 401 unauthorized, 500 server, fetch failure network, 201 without a key bad_response', async () => {
    expect(await code(client(jest.fn(async () => res(403, {}))).create('x'))).toBe('premium_required');
    expect(await code(client(jest.fn(async () => res(401, {}))).create('x'))).toBe('unauthorized');
    expect(await code(client(jest.fn(async () => res(500, {}))).create('x'))).toBe('server');
    expect(await code(client(jest.fn(async () => { throw new Error('offline'); })).create('x'))).toBe('network');
    expect(await code(client(jest.fn(async () => res(201, { id: 'k-1', prefix: 'p' }))).create('x'))).toBe('bad_response');
  });

  test('no token: unauthorized and no request is made', async () => {
    const f = jest.fn();
    expect(await code(client(f, null).create('x'))).toBe('unauthorized');
    expect(await code(client(f, null).list())).toBe('unauthorized');
    expect(await code(client(f, null).revoke('k-1'))).toBe('unauthorized');
    expect(f).not.toHaveBeenCalled();
  });

  test('list: GET of the granted columns only (no key, no hash), mapped to camelCase', async () => {
    const f = jest.fn(async () => res(200, [row, { ...row, id: 'k-2', revoked_at: '2026-11-24T11:00:00Z', last_used_at: '2026-11-24T10:30:00Z' }]));
    const out = await client(f).list();
    expect(out).toHaveLength(2);
    expect(out[1]).toEqual({ id: 'k-2', name: 'n', prefix: 'nwk_TEST', createdAt: '2026-11-24T10:00:00Z', lastUsedAt: '2026-11-24T10:30:00Z', revokedAt: '2026-11-24T11:00:00Z' });
    const [url, init] = f.mock.calls[0] as unknown as [string, RequestInit];
    expect(url).toBe(apiKeysListUrl(base));
    expect(url).toContain('/rest/v1/api_keys?select=id,name,prefix,created_at,last_used_at,revoked_at');
    expect(url).not.toMatch(/key_hash|owner_id/);
    expect(init.method).toBe('GET');
  });

  test('list: non-array or incomplete rows are bad_response, never an empty list', async () => {
    expect(await code(client(jest.fn(async () => res(200, { rows: [] }))).list())).toBe('bad_response');
    expect(await code(client(jest.fn(async () => res(200, [{ id: 'k' }]))).list())).toBe('bad_response');
    expect(await code(client(jest.fn(async () => res(200))).list())).toBe('bad_response');
    expect(await code(client(jest.fn(async () => res(500, {}))).list())).toBe('server');
  });

  test('revoke: DELETE /functions/v1/api-keys/{id} resolves on 204, 404 not_found, other errors mapped', async () => {
    const f = jest.fn(async () => res(204));
    await client(f).revoke('a/b');
    const [url, init] = f.mock.calls[0] as unknown as [string, RequestInit];
    expect(url).toBe(`${base}/functions/v1/api-keys/a%2Fb`);
    expect(init.method).toBe('DELETE');
    expect(await code(client(jest.fn(async () => res(404, {}))).revoke('k'))).toBe('not_found');
    expect(await code(client(jest.fn(async () => res(200, {}))).revoke('k'))).toBe('unknown');
    expect(await code(client(jest.fn(async () => res(503, {}))).revoke('k'))).toBe('server');
  });

  test('unconfigured service reports not_configured for every call', async () => {
    expect(await code(unconfiguredApiKeys.list())).toBe('not_configured');
    expect(await code(unconfiguredApiKeys.create('x'))).toBe('not_configured');
    expect(await code(unconfiguredApiKeys.revoke('x'))).toBe('not_configured');
  });
});

describe('key name validation (openapi: name required, maxLength 60)', () => {
  test('required, trimmed, at most 60', () => {
    expect(validateKeyName('')?.key).toBe('mcp.keys.name.required');
    expect(validateKeyName('   ')?.key).toBe('mcp.keys.name.required');
    expect(validateKeyName('a'.repeat(60))).toBeNull();
    expect(validateKeyName('a'.repeat(61))?.key).toBe('mcp.keys.name.long');
  });
});
