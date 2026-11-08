// Supabase edge function `claim-token` (Deno). Logic and requirement IDs: ../_shared/handlers.ts. Contract: docs/interfaces/openapi.yaml.
import { handleClaimToken } from "../_shared/handlers.ts";
import { makeDeps } from "../_shared/supabase.ts";

Deno.serve((req) => handleClaimToken(req, makeDeps()));
