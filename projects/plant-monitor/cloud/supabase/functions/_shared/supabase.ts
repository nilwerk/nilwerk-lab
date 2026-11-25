// Wires Deps to Supabase. Keys come from the environment ONLY; nothing is hard-coded or logged.
// Name order (env.ts): SUPABASE_SECRET_KEY, then SUPABASE_SERVICE_ROLE_KEY; SUPABASE_PUBLISHABLE_KEY, then SUPABASE_ANON_KEY.
// The hosted runtime injects the legacy names (reported by the Lead after the 2026-11-16 deploy), hence the fallback. See README "Production".
import { createClient } from "npm:@supabase/supabase-js@2.45.4";
import type { Deps, RpcResult } from "./lib.ts";
import { envFirst, PUBLISHABLE_KEY_NAMES, SECRET_KEY_NAMES } from "./env.ts";
import type { AnalyticsDeps } from "./analytics.ts";
import { buildAnalyticsDeps, type AnalyticsClient } from "./analytics_deps.ts";
import type { ApiKeysDeps } from "./api_keys.ts";
import { buildApiKeysDeps, type KeysClient } from "./api_keys_deps.ts";

const env = (...names: readonly string[]): string => envFirst((n) => Deno.env.get(n), names);

export function makeDeps(): Deps {
  const url = env("SUPABASE_URL");
  // service client: bypasses RLS, used only to call the service_role-only functions of migration 20261108000004
  const admin = createClient(url, env(...SECRET_KEY_NAMES), { auth: { persistSession: false, autoRefreshToken: false } });
  return {
    async rpc(name, args): Promise<RpcResult> {
      const { data, error } = await admin.rpc(name, args);
      return { data, error: error ? { message: error.message } : null };
    },
    async getUserId(jwt) {
      const pub = createClient(url, env(...PUBLISHABLE_KEY_NAMES), { auth: { persistSession: false, autoRefreshToken: false } });
      const { data, error } = await pub.auth.getUser(jwt);
      return error || !data.user ? null : data.user.id;
    },
    randomBytes: (n) => crypto.getRandomValues(new Uint8Array(n)),
    // DELETE /account (NFR-07). UNVERIFIED against a live project, like the rest of this file.
    async deleteUserPhotos(userId, knownPaths) {
      const bucket = admin.storage.from("plant-photos");
      const found = new Set(knownPaths.filter((p) => p.startsWith(`${userId}/`)));
      const walk = async (prefix: string): Promise<{ message: string } | null> => {   // '<uid>/<plant_id>/<uuid>.jpg': two levels
        for (let offset = 0; ; offset += 100) {
          const { data, error } = await bucket.list(prefix, { limit: 100, offset });
          if (error) return { message: error.message };
          for (const o of data ?? []) {
            if (o.id === null) { const e = await walk(`${prefix}/${o.name}`); if (e) return e; }   // folder
            else found.add(`${prefix}/${o.name}`);
          }
          if (!data || data.length < 100) return null;
        }
      };
      const e = await walk(userId);
      if (e) return e;
      const all = [...found];
      for (let i = 0; i < all.length; i += 100) {
        const { error } = await bucket.remove(all.slice(i, i + 100));
        if (error) return { message: error.message };
      }
      return null;
    },
    // GET /export (NFR-07). UNVERIFIED against a live project.
    async signPhotoUrls(paths, expiresInSeconds) {
      const urls: Record<string, string | null> = {};
      for (let i = 0; i < paths.length; i += 100) {
        const chunk = paths.slice(i, i + 100);
        const { data, error } = await admin.storage.from("plant-photos").createSignedUrls(chunk, expiresInSeconds);
        if (error || !data) return { error: { message: error?.message ?? "no data" } };
        for (const p of chunk) urls[p] = null;
        for (const o of data) if (o.path && !o.error && o.signedUrl) urls[o.path] = o.signedUrl;
      }
      return { urls };
    },
    async deleteAuthUser(userId) {
      const { error } = await admin.auth.admin.deleteUser(userId);
      if (error && !/not.?found/i.test(error.message) && (error as { status?: number }).status !== 404) return { message: error.message };
      return null;
    },
  };
}

/**
 * Deps for GET /analytics (4.B4 slice 2; FR-P01, FR-P04, NFR-06). Every call carries the USER's JWT, never the service key: RLS and
 * public.is_premium() then see auth.uid() = the caller. No service-role query exists on this path. UNVERIFIED against a live project.
 */
export function makeAnalyticsDeps(): AnalyticsDeps {
  const url = env("SUPABASE_URL");
  const pubKey = env(...PUBLISHABLE_KEY_NAMES);
  const asUser = (jwt: string) => createClient(url, pubKey, {
    global: { headers: { Authorization: `Bearer ${jwt}` } },
    auth: { persistSession: false, autoRefreshToken: false },
  });
  // The query logic lives in analytics_deps.ts (no npm: import, so Node tests can load it with a fake client).
  return buildAnalyticsDeps(asUser as unknown as (jwt: string) => AnalyticsClient);
}

/**
 * Deps for POST/DELETE /api-keys (4.B2d; FR-P03, FR-P04, NFR-06). The premium check and the ownership read carry the USER's JWT (RLS applies).
 * The two writes use the service-role client because db-schema.sql grants authenticated no insert/update on api_keys; each is filtered by the
 * verified caller's id. UNVERIFIED against a live project.
 */
export function makeApiKeysDeps(): ApiKeysDeps {
  const url = env("SUPABASE_URL");
  const pubKey = env(...PUBLISHABLE_KEY_NAMES);
  const asUser = (jwt: string) => createClient(url, pubKey, {
    global: { headers: { Authorization: `Bearer ${jwt}` } },
    auth: { persistSession: false, autoRefreshToken: false },
  });
  const admin = () => createClient(url, env(...SECRET_KEY_NAMES), { auth: { persistSession: false, autoRefreshToken: false } });
  return buildApiKeysDeps(asUser as unknown as (jwt: string) => KeysClient, admin as unknown as () => KeysClient, (n) => crypto.getRandomValues(new Uint8Array(n)));
}
