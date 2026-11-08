// In-memory AuthService: the "local/mocked Supabase" for tests and for running the app without a backend (EXPO_PUBLIC_MOCK_AUTH=1).
import { AuthError, type AuthService, type AuthUser, type Profile } from './types';

interface Account { id: string; email: string; password: string; profile: Profile }

export interface FakeAuthOptions {
  needsConfirmation?: boolean;
  failNext?: AuthError;
  deleteFails?: boolean;
}

export function createFakeAuth(opts: FakeAuthOptions = {}): AuthService & { accounts: Account[]; options: FakeAuthOptions } {
  const accounts: Account[] = [];
  let current: AuthUser | null = null;
  const listeners = new Set<(u: AuthUser | null) => void>();
  const emit = () => listeners.forEach((l) => l(current));
  const maybeFail = () => { if (opts.failNext) { const e = opts.failNext; opts.failNext = undefined; throw e; } };
  const me = () => { const a = accounts.find((x) => x.id === current?.id); if (!a) throw new AuthError('unknown'); return a; };

  return {
    accounts,
    options: opts,
    async getSession() { return current; },
    onChange(cb) { listeners.add(cb); return () => { listeners.delete(cb); }; },
    async signUp(email, password, displayName) {
      maybeFail();
      const e = email.trim().toLowerCase();
      if (accounts.some((a) => a.email === e)) throw new AuthError('email_taken');
      const acc: Account = { id: `user-${accounts.length + 1}`, email: e, password, profile: { displayName: displayName?.trim() || null, isPremium: false } };
      accounts.push(acc);
      if (opts.needsConfirmation) return { user: null, needsConfirmation: true };
      current = { id: acc.id, email: acc.email };
      emit();
      return { user: current, needsConfirmation: false };
    },
    async signIn(email, password) {
      maybeFail();
      const a = accounts.find((x) => x.email === email.trim().toLowerCase() && x.password === password);
      if (!a) throw new AuthError('invalid_credentials');
      current = { id: a.id, email: a.email };
      emit();
      return current;
    },
    async signOut() { maybeFail(); current = null; emit(); },
    async getProfile() { maybeFail(); return { ...me().profile }; },
    async updateDisplayName(name) { maybeFail(); me().profile.displayName = name.trim() || null; },
    async deleteAccount() {
      if (opts.deleteFails) throw new AuthError('network');
      const a = me();
      accounts.splice(accounts.indexOf(a), 1);
      current = null;
      emit();
    },
  };
}
