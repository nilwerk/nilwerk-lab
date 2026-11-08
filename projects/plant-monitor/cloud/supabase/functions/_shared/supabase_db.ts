// Db implementation over supabase-js (service role, runs only inside the Edge Function; never in tests).
// Secrets by NAME only: SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY are injected by Supabase at runtime.
// NOT RUN in the 4.B2 session (no Deno / Supabase CLI / project): see cloud/README.md "Not run".
import { createClient } from "npm:@supabase/supabase-js@2.45.4";
import { type Db, DbError } from "./handlers.ts";

export function supabaseDb(): Db {
  const sb = createClient(Deno.env.get("SUPABASE_URL")!, Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!, { auth: { persistSession: false } });
  const call = async (fn: string, args: Record<string, unknown>) => {
    const { data, error } = await sb.rpc(fn, args);
    if (error) throw new DbError(error.code ?? "unknown", error.message);   // PostgREST passes the SQLSTATE (NW401/NW409/NW403)
    return data;
  };
  return {
    async authenticate(h) { const rows = await call("authenticate_device", { p_token_hash: h }); return rows[0]; },
    claim: (a) => call("claim_device", { p_hw_id: a.hw_id, p_claim_hash: a.claim_hash, p_name: a.name, p_fw: a.fw, p_token_hash: a.token_hash }),
    ingest: (id, report, at) => call("ingest_report", { p_device: id, p_report: report, p_received: at }),
    async signUrl(path) {
      const { data, error } = await sb.storage.from("firmware").createSignedUrl(path, 3600);   // valid 1 h (openapi Artifact)
      if (error) throw new DbError("storage", error.message);
      return data.signedUrl;
    },
  };
}
