// Auth contract used by the UI. Two implementations: supabaseAuth.ts (real) and fakeAuth.ts (tests / local mock).
// Requirements: FR-A01 (account: sign up, sign in, profile, sign out, delete), NFR-06 (RLS: the app only ever reads its own rows), NFR-07 (delete removes all data).

export interface AuthUser { id: string; email: string }
export interface Profile { displayName: string | null; isPremium: boolean }

export type AuthErrorCode = 'invalid_credentials' | 'email_taken' | 'network' | 'not_configured' | 'unauthorized' | 'server' | 'unknown';

export class AuthError extends Error {
  code: AuthErrorCode;
  constructor(code: AuthErrorCode, message?: string) {
    super(message ?? code);
    this.name = 'AuthError';
    this.code = code;
  }
}

export interface SignUpResult { user: AuthUser | null; needsConfirmation: boolean }

export interface AuthService {
  getSession(): Promise<AuthUser | null>;
  /** Called when the session changes (sign in, sign out, token refresh failure). Returns an unsubscribe function. */
  onChange(cb: (user: AuthUser | null) => void): () => void;
  signUp(email: string, password: string, displayName?: string): Promise<SignUpResult>;
  signIn(email: string, password: string): Promise<AuthUser>;
  signOut(): Promise<void>;
  getProfile(): Promise<Profile>;
  updateDisplayName(name: string): Promise<void>;
  /** DELETE /account with {confirm:"DELETE"} (openapi.yaml /account, edge function delete-account), then drops the local session. Rejects with AuthError: unauthorized (401 / no session), network, server (5xx), unknown. The export-before-delete gate is the caller's job (src/export/exportGate.ts deleteAccountGated). */
  deleteAccount(): Promise<void>;
}
