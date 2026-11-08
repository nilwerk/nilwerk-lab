// POST /device-claim (FR-D03, FR-A03, FR-A08, NFR-06). Deploy with --no-verify-jwt: the caller is a sensor, auth = claim token.
import { handleClaim } from "../_shared/handlers.ts";
import { supabaseDb } from "../_shared/supabase_db.ts";

const db = supabaseDb();
Deno.serve(async (req) => {
  if (req.method !== "POST") return new Response(JSON.stringify({ error: "method_not_allowed" }), { status: 405 });
  try {
    const out = await handleClaim(await req.text(), db);
    return new Response(JSON.stringify(out.body), { status: out.status, headers: { "content-type": "application/json" } });
  } catch (e) {
    console.error("device-claim", (e as Error).message);          // never log tokens or bodies (NFR-06)
    return new Response(JSON.stringify({ error: "internal" }), { status: 500 });
  }
});
