// Key-name resolution, split out of supabase.ts so it can be unit-tested without Deno or npm: imports. Names only, never values.
// The hosted Supabase function runtime injects the LEGACY names (SUPABASE_SERVICE_ROLE_KEY, SUPABASE_ANON_KEY); the new-model names
// (A-035) are preferred when set, e.g. for local runs or a future runtime.
export type EnvGet = (name: string) => string | undefined;

export function envFirst(get: EnvGet, names: readonly string[]): string {
  for (const n of names) { const v = get(n); if (v) return v; }
  throw new Error(`missing environment variable: set ${names.join(" or ")}`);
}

export const SECRET_KEY_NAMES = ["SUPABASE_SECRET_KEY", "SUPABASE_SERVICE_ROLE_KEY"] as const;
export const PUBLISHABLE_KEY_NAMES = ["SUPABASE_PUBLISHABLE_KEY", "SUPABASE_ANON_KEY"] as const;
