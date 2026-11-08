// FR-A01 auth state machine + storage chunking + fake service flow
import { authReducer, initialAuthState } from '../auth/authState';
import { createFakeAuth } from '../auth/fakeAuth';
import { chunked, type KeyValueStore } from '../auth/storage';
import { AuthError } from '../auth/types';
import { isConfigured, readConfig } from '../config';

const u = { id: 'u1', email: 'a@b.de' };

describe('authReducer', () => {
  test('starts loading, session -> signedIn, none -> signedOut', () => {
    expect(initialAuthState.status).toBe('loading');
    const a = authReducer(initialAuthState, { type: 'session', user: u });
    expect(a).toEqual({ status: 'signedIn', user: u });
    expect(authReducer(a, { type: 'session', user: null })).toEqual({ status: 'signedOut', user: null });
    expect(authReducer(initialAuthState, { type: 'session', user: null }).status).toBe('signedOut');
  });
  test('same session keeps the same object (no re-render churn); a different user replaces it', () => {
    const a = authReducer(initialAuthState, { type: 'session', user: u });
    expect(authReducer(a, { type: 'session', user: { ...u } })).toBe(a);
    expect(authReducer(a, { type: 'session', user: { id: 'u2', email: 'c@d.de' } }).user?.id).toBe('u2');
  });
  test('signedOut action is idempotent', () => {
    const s = authReducer(initialAuthState, { type: 'signedOut' });
    expect(authReducer(s, { type: 'signedOut' })).toBe(s);
  });
});

describe('fake auth service (local mock of Supabase)', () => {
  test('sign up, sign out, sign in, wrong password, duplicate', async () => {
    const s = createFakeAuth();
    const seen: Array<string | null> = [];
    s.onChange((x) => seen.push(x?.email ?? null));
    const r = await s.signUp('Sam@Example.com', 'secret-123', 'Sam');
    expect(r.user?.email).toBe('sam@example.com');
    expect(await s.getProfile()).toEqual({ displayName: 'Sam', isPremium: false });
    await s.signOut();
    await expect(s.signIn('sam@example.com', 'wrong')).rejects.toMatchObject({ code: 'invalid_credentials' });
    await expect(s.signUp('sam@example.com', 'secret-123')).rejects.toMatchObject({ code: 'email_taken' });
    expect((await s.signIn('sam@example.com', 'secret-123')).id).toBe('user-1');
    expect(seen).toEqual(['sam@example.com', null, 'sam@example.com']);
  });
  test('email confirmation on: sign up gives no session', async () => {
    const s = createFakeAuth({ needsConfirmation: true });
    expect(await s.signUp('a@b.de', 'secret-123')).toEqual({ user: null, needsConfirmation: true });
    expect(await s.getSession()).toBeNull();
  });
  test('delete account removes the account and ends the session; failure removes nothing', async () => {
    const s = createFakeAuth();
    await s.signUp('a@b.de', 'secret-123');
    s.options.deleteFails = true;
    await expect(s.deleteAccount()).rejects.toBeInstanceOf(AuthError);
    expect(s.accounts).toHaveLength(1);
    s.options.deleteFails = false;
    await s.deleteAccount();
    expect(s.accounts).toHaveLength(0);
    expect(await s.getSession()).toBeNull();
    await expect(s.signIn('a@b.de', 'secret-123')).rejects.toMatchObject({ code: 'invalid_credentials' });
  });
});

describe('chunked storage (session > 2 KB)', () => {
  const mem = (): KeyValueStore & { data: Map<string, string> } => {
    const data = new Map<string, string>();
    return { data, getItem: async (k) => data.get(k) ?? null, setItem: async (k, v) => { data.set(k, v); }, removeItem: async (k) => { data.delete(k); } };
  };
  test('round trip, overwrite with shorter value leaves no stale parts, remove clears', async () => {
    const base = mem();
    const s = chunked(base, 10);
    const long = 'x'.repeat(95);
    await s.setItem('k', long);
    expect(await s.getItem('k')).toBe(long);
    expect(Math.max(...[...base.data.values()].map((v) => v.length))).toBeLessThanOrEqual(10);
    await s.setItem('k', 'short');
    expect(await s.getItem('k')).toBe('short');
    expect(base.data.size).toBe(2);
    await s.removeItem('k');
    expect(base.data.size).toBe(0);
    expect(await s.getItem('k')).toBeNull();
  });
  test('torn write reads as no session', async () => {
    const base = mem();
    const s = chunked(base, 4);
    await s.setItem('k', 'abcdefghij');
    base.data.delete('k.1');
    expect(await s.getItem('k')).toBeNull();
  });
});

describe('config', () => {
  test('reads names from extra; not configured when empty or non-https', () => {
    expect(isConfigured(readConfig({}))).toBe(false);
    expect(isConfigured(readConfig({ supabaseUrl: 'http://evil.example', supabasePublishableKey: 'k' }))).toBe(false);
    expect(isConfigured(readConfig({ supabaseUrl: 'https://x.supabase.co', supabasePublishableKey: 'sb_publishable_x' }))).toBe(true);
    expect(isConfigured(readConfig({ supabaseUrl: 'http://127.0.0.1:54321', supabasePublishableKey: 'k' }))).toBe(true);
  });
});
