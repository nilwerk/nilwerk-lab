// Supabase edge function `ingest` (Deno). Logic and requirement IDs: ../_shared/handlers.ts. Contract: docs/interfaces/openapi.yaml.
import { handleIngest } from "../_shared/handlers.ts";
import { makeDeps } from "../_shared/supabase.ts";

Deno.serve((req) => handleIngest(req, makeDeps()));
