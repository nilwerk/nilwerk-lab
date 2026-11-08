// FR-A01 auth state machine + storage chunking + fake service flow
import { authReducer, initialAuthState } from '../auth/authState';
import React from 'react';
import { render, screen, waitFor } from '@testing-library/react-native';
import { Text } from 'react-native';
import { AuthProvider, useAuth } from '../auth/AuthContext';
import { createFakeAuth } from '../auth/fakeAuth';
import { chunked, type KeyValueStore } from '../auth/storage';
import { AuthError } from '../auth/types';
import { DEFAULT_CONTACT_EMAIL, isConfigured, readConfig } from '../config';
import { contactUrl } from '../screens/PremiumScreen';
import appConfig from '../../app.config';

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
  test('signedOut action ends the session from every state (A-048 follow-up, QA note #42)', () => {
    const states = [initialAuthState, { status: 'signedIn', user: u } as const, { status: 'signedOut', user: null } as const];
    for (const from of states) expect(authReducer(from, { type: 'signedOut' })).toEqual({ status: 'signedOut', user: null });
  });
  test('unknown action leaves state untouched', () => {
    const a = authReducer(initialAuthState, { type: 'session', user: u });
    expect(authReducer(a, { type: 'nope' } as never)).toBe(a);
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

describe('AuthProvider startup', () => {
  const Probe = () => <Text>{useAuth().state.status}</Text>;
  test('getSession rejection does not leave the app stuck on loading: it ends signedOut', async () => {
    const svc = createFakeAuth();
    svc.getSession = () => Promise.reject(new Error('storage unreadable'));
    await render(<AuthProvider service={svc}><Probe /></AuthProvider>);
    await waitFor(() => expect(screen.getByText('signedOut')).toBeTruthy());
  });
});

describe('contact email (A-048)', () => {
  test('default is the shared Nilwerk mailbox, in the shipped config and when extra is missing', () => {
    expect(DEFAULT_CONTACT_EMAIL).toBe('nilwerk.team@gmail.com');
    expect(readConfig({}).contactEmail).toBe('nilwerk.team@gmail.com');
    expect(readConfig(undefined).contactEmail).toBe('nilwerk.team@gmail.com');
    const saved = process.env.CONTACT_EMAIL;
    delete process.env.CONTACT_EMAIL;
    try {
      expect(appConfig.extra?.contactEmail).toBe(DEFAULT_CONTACT_EMAIL);
    } finally { if (saved !== undefined) process.env.CONTACT_EMAIL = saved; }
  });
  test('override wins; an explicitly empty value stays empty (link hidden)', () => {
    expect(readConfig({ contactEmail: ' team@example.org ' }).contactEmail).toBe('team@example.org');
    expect(readConfig({ contactEmail: '' }).contactEmail).toBe('');
    expect(contactUrl('')).toBeNull();
  });
  test('mailto has the encoded subject (en dash and spaces)', () => {
    expect(contactUrl(DEFAULT_CONTACT_EMAIL)).toBe('mailto:nilwerk.team@gmail.com?subject=Plant%20Monitor%20%E2%80%93%20Premium%20activation');
  });
});
