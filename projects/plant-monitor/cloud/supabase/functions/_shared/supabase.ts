// Wires Deps to Supabase. Keys come from the environment ONLY (A-035 names); nothing is hard-coded or logged.
// UNVERIFIED against a live project (no secrets in the agent session): see README "Production".
import { createClient } from "npm:@supabase/supabase-js@2.45.4";
import type { Deps, RpcResult } from "./lib.ts";

function env(name: string): string {
  const v = Deno.env.get(name);
  if (!v) throw new Error(`missing environment variable ${name}`);
  return v;
}

export function makeDeps(): Deps {
  const url = env("SUPABASE_URL");
  // service client: bypasses RLS, used only to call the service_role-only functions of migration 20261108000004
  const admin = createClient(url, env("SUPABASE_SECRET_KEY"), { auth: { persistSession: false, autoRefreshToken: false } });
  return {
    async rpc(name, args): Promise<RpcResult> {
      const { data, error } = await admin.rpc(name, args);
      return { data, error: error ? { message: error.message } : null };
    },
    async getUserId(jwt) {
      const pub = createClient(url, env("SUPABASE_PUBLISHABLE_KEY"), { auth: { persistSession: false, autoRefreshToken: false } });
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
    async deleteAuthUser(userId) {
      const { error } = await admin.auth.admin.deleteUser(userId);
      if (error && !/not.?found/i.test(error.message) && (error as { status?: number }).status !== 404) return { message: error.message };
      return null;
    },
  };
}
