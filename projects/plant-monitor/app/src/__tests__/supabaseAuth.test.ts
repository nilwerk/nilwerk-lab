// createSupabaseAuth.deleteAccount (FR-A01, NFR-07, NFR-06). QA note from PR #117: the adapter itself had no test, so a hard-coded wrong route would pass.
// Supabase client and fetch are fakes; nothing here touches the live project.
import { createSupabaseAuth } from '../auth/supabaseAuth';
import { AuthError } from '../auth/types';

const mockSignOut = jest.fn();
let mockSession: { access_token: string } | null = { access_token: 'jwt-123' };
jest.mock('@supabase/supabase-js', () => ({
  createClient: () => ({ auth: { getSession: async () => ({ data: { session: mockSession }, error: null }), signOut: (...a: unknown[]) => mockSignOut(...a), onAuthStateChange: () => ({ data: { subscription: { unsubscribe() {} } } }) } }),
}));
jest.mock('expo-secure-store', () => ({ getItemAsync: jest.fn(), setItemAsync: jest.fn(), deleteItemAsync: jest.fn() }));

const cfg = { supabaseUrl: 'https://abc.supabase.co/', supabasePublishableKey: 'sb_publishable_x', contactEmail: '' };
const fetchMock = jest.fn();
beforeEach(() => { mockSession = { access_token: 'jwt-123' }; fetchMock.mockReset(); mockSignOut.mockReset().mockResolvedValue({}); (globalThis as any).fetch = fetchMock; });

describe('supabaseAuth.deleteAccount', () => {
  test('calls DELETE https://<project>/functions/v1/delete-account with bearer, apikey and {confirm:"DELETE"}, then drops the local session', async () => {
    fetchMock.mockResolvedValue({ status: 204 });
    await createSupabaseAuth(cfg).deleteAccount();
    expect(fetchMock).toHaveBeenCalledTimes(1);
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toBe('https://abc.supabase.co/functions/v1/delete-account');
    expect(init.method).toBe('DELETE');
    expect(init.headers).toMatchObject({ Authorization: 'Bearer jwt-123', apikey: 'sb_publishable_x' });
    expect(JSON.parse(init.body)).toEqual({ confirm: 'DELETE' });
    expect(mockSignOut).toHaveBeenCalledWith({ scope: 'local' });
  });
  test('no session -> unauthorized, no request', async () => {
    mockSession = null;
    await expect(createSupabaseAuth(cfg).deleteAccount()).rejects.toMatchObject({ code: 'unauthorized' });
    expect(fetchMock).not.toHaveBeenCalled();
  });
  test.each([[401, 'unauthorized'], [500, 'server'], [400, 'unknown'], [418, 'unknown']])('status %i -> AuthError %s and the local session is kept', async (status, code) => {
    fetchMock.mockResolvedValue({ status });
    const e = await createSupabaseAuth(cfg).deleteAccount().catch((x) => x);
    expect(e).toBeInstanceOf(AuthError);
    expect(e.code).toBe(code);
    expect(mockSignOut).not.toHaveBeenCalled();
  });
  test('fetch failure -> network, mockSession kept', async () => {
    fetchMock.mockRejectedValue(new TypeError('Network request failed'));
    await expect(createSupabaseAuth(cfg).deleteAccount()).rejects.toMatchObject({ code: 'network' });
    expect(mockSignOut).not.toHaveBeenCalled();
  });
});

describe('supabaseAuth.getAccessToken', () => {
  test('returns the mockSession JWT, null when signed out', async () => {
    expect(await createSupabaseAuth(cfg).getAccessToken()).toBe('jwt-123');
    mockSession = null;
    expect(await createSupabaseAuth(cfg).getAccessToken()).toBeNull();
  });
});
