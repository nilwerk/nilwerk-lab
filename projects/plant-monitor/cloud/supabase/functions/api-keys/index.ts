// Supabase edge function `api-keys` (Deno), served as POST /api-keys and DELETE /api-keys/{id} (task 4.B2d; FR-P03, FR-P04, NFR-06). Logic: ../_shared/api_keys.ts.
import { handleApiKeys } from "../_shared/api_keys.ts";
import { makeApiKeysDeps } from "../_shared/supabase.ts";

Deno.serve((req) => handleApiKeys(req, makeApiKeysDeps()));
