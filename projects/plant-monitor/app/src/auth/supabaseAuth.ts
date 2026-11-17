// Real Supabase implementation of AuthService (FR-A01). NOT run against a real backend in the agent session (no project exists, A-025).
import { createClient, type SupabaseClient, type User } from '@supabase/supabase-js';
import { Platform } from 'react-native';
import * as SecureStore from 'expo-secure-store';
import { AuthError, type AuthService, type AuthUser, type Profile } from './types';
import { chunked, type KeyValueStore } from './storage';
import type { AppConfig } from '../config';
import { AccountApiError, deleteAccountApi } from '../account/accountApi';

const secureStore: KeyValueStore = {
  getItem: (k) => SecureStore.getItemAsync(k),
  setItem: (k, v) => SecureStore.setItemAsync(k, v),
  removeItem: (k) => SecureStore.deleteItemAsync(k),
};

const webStore: KeyValueStore = {
  async getItem(k) { try { return globalThis.localStorage?.getItem(k) ?? null; } catch { return null; } },
  async setItem(k, v) { try { globalThis.localStorage?.setItem(k, v); } catch { /* storage blocked */ } },
  async removeItem(k) { try { globalThis.localStorage?.removeItem(k); } catch { /* storage blocked */ } },
};

const toUser = (u: User | null | undefined): AuthUser | null => (u ? { id: u.id, email: u.email ?? '' } : null);

function mapError(e: unknown): AuthError {
  if (e instanceof AuthError) return e;
  const err = e as { code?: string; name?: string; message?: string; status?: number } | null;
  const code = err?.code ?? '';
  if (code === 'invalid_credentials') return new AuthError('invalid_credentials');
  if (code === 'user_already_exists' || code === 'email_exists') return new AuthError('email_taken');
  if (err?.name === 'AuthRetryableFetchError' || err?.status === 0 || err?.message === 'Network request failed' || err instanceof TypeError) return new AuthError('network');
  return new AuthError('unknown', err?.message);
}

export function createSupabaseAuth(cfg: AppConfig): AuthService {
  const client: SupabaseClient = createClient(cfg.supabaseUrl, cfg.supabasePublishableKey, {
    auth: {
      storage: chunked(Platform.OS === 'web' ? webStore : secureStore),
      autoRefreshToken: true,
      persistSession: true,
      detectSessionInUrl: false,
    },
  });

  return {
    async getSession() {
      const { data, error } = await client.auth.getSession();
      if (error) throw mapError(error);
      return toUser(data.session?.user);
    },
    onChange(cb) {
      const { data } = client.auth.onAuthStateChange((_event, session) => cb(toUser(session?.user)));
      return () => data.subscription.unsubscribe();
    },
    async signUp(email, password, displayName) {
      const name = displayName?.trim();
      const { data, error } = await client.auth.signUp({ email: email.trim(), password, options: name ? { data: { display_name: name } } : undefined });
      if (error) throw mapError(error);
      // Supabase hides "already registered" with an empty identities list when confirmations are on.
      if (data.user && Array.isArray(data.user.identities) && data.user.identities.length === 0) throw new AuthError('email_taken');
      return { user: toUser(data.session?.user), needsConfirmation: !data.session };
    },
    async signIn(email, password) {
      const { data, error } = await client.auth.signInWithPassword({ email: email.trim(), password });
      if (error) throw mapError(error);
      const u = toUser(data.user);
      if (!u) throw new AuthError('unknown');
      return u;
    },
    async signOut() {
      const { error } = await client.auth.signOut();
      if (error) throw mapError(error);
    },
    async getProfile(): Promise<Profile> {
      const { data: ures, error: uerr } = await client.auth.getUser();
      if (uerr || !ures.user) throw mapError(uerr);
      // RLS: profiles_select_own (db-schema.sql), so this can only return the caller's row (NFR-06).
      const { data, error } = await client.from('profiles').select('display_name, is_premium').eq('id', ures.user.id).single();
      if (error) throw mapError(error);
      let displayName: string | null = data.display_name;
      // handle_new_user() only inserts the id, so the name typed at sign-up (kept in user metadata) is copied once here.
      const metaName = ures.user.user_metadata?.display_name;
      if (!displayName && typeof metaName === 'string' && metaName.trim()) {
        const { error: uerr2 } = await client.from('profiles').update({ display_name: metaName.trim() }).eq('id', ures.user.id);
        if (!uerr2) displayName = metaName.trim();
      }
      return { displayName, isPremium: data.is_premium === true };
    },
    async updateDisplayName(name) {
      const { data: ures, error: uerr } = await client.auth.getUser();
      if (uerr || !ures.user) throw mapError(uerr);
      const { error } = await client.from('profiles').update({ display_name: name.trim() || null }).eq('id', ures.user.id);
      if (error) throw mapError(error);
    },
    async deleteAccount() {
      const { data, error } = await client.auth.getSession();
      if (error) throw mapError(error);
      if (!data.session) throw new AuthError('unauthorized');
      try {
        await deleteAccountApi({ baseUrl: cfg.supabaseUrl, publishableKey: cfg.supabasePublishableKey, accessToken: data.session.access_token });
      } catch (e) {
        if (e instanceof AccountApiError) throw new AuthError(e.code === 'bad_request' ? 'unknown' : e.code, e.message);
        throw mapError(e);
      }
      await client.auth.signOut({ scope: 'local' }).catch(() => undefined);
    },
  };
}
