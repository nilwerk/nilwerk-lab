// Supabase edge function `mcp` (task 4.B5): the MCP server endpoint for the user's AI client (FR-P03). Logic and requirement IDs: ../_shared/mcp.ts.
// verify_jwt = false: the bearer token is the user's own API key (nwk_...), checked in the function against api_keys (NFR-06).
import { handleMcp } from "../_shared/mcp.ts";
import { makeDeps } from "../_shared/supabase.ts";

Deno.serve((req) => handleMcp(req, makeDeps()));
