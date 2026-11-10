// Supabase edge function `delete-account` (Deno), served as DELETE /account (4.B2b; FR-A01, NFR-07). Logic and requirement IDs: ../_shared/handlers.ts. Contract: docs/interfaces/openapi.yaml.
import { handleDeleteAccount } from "../_shared/handlers.ts";
import { makeDeps } from "../_shared/supabase.ts";

Deno.serve((req) => handleDeleteAccount(req, makeDeps()));
