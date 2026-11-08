// Supabase edge function `device-claim` (Deno). Logic and requirement IDs: ../_shared/handlers.ts. Contract: docs/interfaces/openapi.yaml.
import { handleDeviceClaim } from "../_shared/handlers.ts";
import { makeDeps } from "../_shared/supabase.ts";

Deno.serve((req) => handleDeviceClaim(req, makeDeps()));
