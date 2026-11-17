// DELETE /account client (FR-A01, NFR-07, NFR-06). Fake fetch only: no network, no Supabase. Contract: docs/interfaces/openapi.yaml /account.
import { AccountApiError, deleteAccountApi, deleteAccountUrl } from '../account/accountApi';

const BASE = 'https://example-project.supabase.invalid/';
const mk = (res: { status: number } | Error) => {
  const calls: { url: string; init: RequestInit }[] = [];
  const fetchImpl = (async (url: string, init: RequestInit) => { calls.push({ url, init }); if (res instanceof Error) throw res; return { status: res.status } as Response; }) as unknown as typeof fetch;
  return { calls, fetchImpl };
};
const call = (fetchImpl: typeof fetch, accessToken = 'jwt-1') => deleteAccountApi({ baseUrl: BASE, publishableKey: 'pub-key', accessToken, fetchImpl });

test('calls the deployed function route delete-account (not /account) with method, bearer, apikey and the fixed body', async () => {
  const { calls, fetchImpl } = mk({ status: 204 });
  await call(fetchImpl);
  expect(calls).toHaveLength(1);
  expect(calls[0].url).toBe('https://example-project.supabase.invalid/functions/v1/delete-account');
  expect(deleteAccountUrl('https://x.invalid')).toBe('https://x.invalid/functions/v1/delete-account');
  expect(calls[0].init.method).toBe('DELETE');
  expect(calls[0].init.headers).toMatchObject({ Authorization: 'Bearer jwt-1', apikey: 'pub-key', 'Content-Type': 'application/json' });
  expect(JSON.parse(calls[0].init.body as string)).toEqual({ confirm: 'DELETE' }); // no user id in the body (NFR-06)
});

test.each([
  [401, 'unauthorized'], [400, 'bad_request'], [405, 'bad_request'], [413, 'bad_request'], [500, 'server'], [503, 'server'], [404, 'unknown'], [200, 'unknown'],
])('status %i -> %s', async (status, code) => {
  const { fetchImpl } = mk({ status });
  await expect(call(fetchImpl)).rejects.toMatchObject({ name: 'AccountApiError', code, status });
});

test('a failed request (offline, DNS, TLS) is a network error', async () => {
  const { fetchImpl } = mk(new TypeError('Network request failed'));
  await expect(call(fetchImpl)).rejects.toMatchObject({ code: 'network' });
});

test('no access token: unauthorized without calling the server', async () => {
  const { calls, fetchImpl } = mk({ status: 204 });
  await expect(call(fetchImpl, '')).rejects.toBeInstanceOf(AccountApiError);
  expect(calls).toHaveLength(0);
});
