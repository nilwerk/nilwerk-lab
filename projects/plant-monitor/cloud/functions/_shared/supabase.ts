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
  };
}
