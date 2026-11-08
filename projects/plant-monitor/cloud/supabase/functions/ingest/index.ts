// POST /ingest (FR-D01, FR-D02, FR-D04, FR-D05, FR-D06, FR-E03, FR-A07, NFR-04, NFR-06). Deploy with --no-verify-jwt:
// the caller is a sensor, auth = per-device bearer token checked against its SHA-256 in device_credentials.
// Not yet implemented (see README): rate limit 6/h per device (openapi, [proposed]) and push dispatch.
import { handleIngest } from "../_shared/handlers.ts";
import { supabaseDb } from "../_shared/supabase_db.ts";

const db = supabaseDb();
Deno.serve(async (req) => {
  if (req.method !== "POST") return new Response(JSON.stringify({ error: "method_not_allowed" }), { status: 405 });
  try {
    const out = await handleIngest(req.headers.get("authorization"), await req.text(), db);
    return new Response(JSON.stringify(out.body), { status: out.status, headers: { "content-type": "application/json" } });
  } catch (e) {
    console.error("ingest", (e as Error).message);
    return new Response(JSON.stringify({ error: "internal" }), { status: 500 });
  }
});
