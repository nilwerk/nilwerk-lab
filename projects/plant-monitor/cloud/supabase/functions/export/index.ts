// Supabase edge function `export` (Deno), served as GET /export (4.B2c; NFR-07, FR-A01). Logic and requirement IDs: ../_shared/export.ts. Contract: docs/interfaces/openapi.yaml.
import { handleExport } from "../_shared/export.ts";
import { makeDeps } from "../_shared/supabase.ts";

Deno.serve((req) => handleExport(req, makeDeps()));
